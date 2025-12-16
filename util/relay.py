from __future__ import annotations
from dataclasses import dataclass
from threading import Lock
from datetime import datetime, timedelta
# from test.plates import relayOFF, relayON
from piplates.RELAYplate import relayOFF, relayON
from time import sleep
from typing import Any, Callable

from flask import current_app

from util.persist import PersistentMapping
from util.singleton import singleton
from util.timmy import Timmy


@dataclass
class Dependency:
    """
    Data class for keeping track of relays other relays need to have
    turned on as dependencies
    """
    relay: Relay
    spin_up: int = 0


class Relay:
    """
    Class that couples relays to timers and to other relays
    """

    logger = current_app.logger

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        board: Any,
        index: int,
        max_time: int,
        default_time: int,
        active: bool,
        visible: bool,
        requires: list[Dependency] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.board = board
        self.index = index
        self.max_time = max_time
        self.default_time = default_time
        self.active = active
        self.visible = visible
        self.requires = requires
        self.timer = Timmy(self.name)
        self.counter = 0
        self.mutex = Lock()
        Relay.logger.debug(" ".join(["Relay", str(self.name), "initialized"]))

    def __str__(self):
        return self.id

    def on(
        self,
        interval: timedelta = None,
        callback: Callable[[...], Any] = None,
        args: list[str] = None,
    ) -> None:
        """
        Increment the counter
        Turns on the relay if the counter was initially zero
        """
        self.mutex.acquire()
        if self.counter == 0:
            if self.requires is not None:
                for dep in self.requires:
                    dep.relay.on()
                    sleep(dep.spin_up)
            relayON(self.board.index, self.index)
        #  We elect to not increment if the timer is changed when already set
        if interval is None or self.timer.is_set() is False:
            self.counter += 1
        if interval is not None:
            self.timer.set(
                interval, self.off if callback is None else callback, args)
        self.mutex.release()
        Relay.logger.info(" ".join(["Relay", str(self.name), "on"]))

    def off(self) -> None:
        """
        Decrement the counter
        Turns off the relay if the counter is reduced to zero
        """
        self.mutex.acquire()
        self.counter -= 1
        if self.counter == 0:
            if self.requires is not None:
                for dep in self.requires:
                    dep.relay.off()
            relayOFF(self.board.index, self.index)
            self.timer.clear()
        self.mutex.release()
        Relay.logger.info(" ".join(["Relay", str(self.name), "off"]))


@singleton
class Baton(PersistentMapping):
    """
    Class for keeping track of Relay objects
    """

    default_filename = "relays"
    logger = current_app.logger

    def __init__(self, filename: str = default_filename):
        super().__init__(filename)
        for relay in self.collection.values():
            relay.board[relay.index] = relay

    def __delitem__(self, key):
        for dep in self.collection[key].requires:
            del dep
        del self.collection[key].board[self.collection[key].index]
        super().__delitem__(key)

    def state(self):
        """
        Method that indicates which Relay objects have their timers set.
        Returns a dict that can be passed as an argument to the dashboard view
        """
        active = {
            id: relay.timer.remaining().total_seconds()
            for id, relay in self.collection.items()
            if relay.timer.is_set()
        }
        Baton.logger.debug(
            " ".join(
                [
                    "Returned get_state() with",
                    "no relays active" if len(active) == 0 else "active relays"
                ] + [self.collection[relay].name for relay in active]
            )
        )
        return active

    def to_obj(self, collection: dict[str, dict]) -> dict[str, Relay]:
        from util.board import Holder
        boards = Holder()
        objects = {}
        while len(objects.keys()) < len(collection.keys()):
            new_objects = {
                id: Relay(
                    id, relay["name"],
                    relay["description"],
                    boards[relay["board"]],
                    relay["index"],
                    relay["max_time"],
                    relay["default_time"],
                    relay["active"],
                    relay["visible"],
                    [
                        Dependency(
                            objects[dep["relay"]],
                            dep["spin_up"]
                        )
                        for dep in relay["requires"]
                    ]
                )
                for id, relay in collection.items()
                if [
                    dep for dep in relay["requires"]
                    if dep["relay"] not in objects.keys()
                ] == []
                and id not in objects.keys()
            }
            if new_objects == {}:
                break
            else:
                objects |= new_objects
        return objects

    def to_json(self, collection: dict[str, Relay]):
        return {
            id: {
                "description": relay.description,
                "name": relay.name,
                "modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
                "board": relay.board.id,
                "index": relay.index,
                "max_time": relay.max_time,
                "default_time": relay.default_time,
                "active": relay.active,
                "visible": relay.visible,
                "requires": [
                    {
                        "relay": dep.relay.id,
                        "spin_up": dep.spin_up
                    }
                    for dep in relay.requires
                ]
            }
            for id, relay in collection.items()
        }
