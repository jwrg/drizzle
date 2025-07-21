"""
    Relay helper classes for Pi-Plates RelayPlate
"""
from __future__ import annotations
from dataclasses import dataclass
from threading import Lock
from datetime import timedelta
from test.plates import relayOFF, relayON
from time import sleep
from typing import Any, Callable

from flask import current_app

from util.timmy import Timmy


@dataclass
class Dependency:
    """
    Helper class for keeping track of relays other relays need to be
    turned on as dependencies
    """
    relay: Relay
    spin_up: int = 0


class Relay:
    """
    Helper class that couples relays to timers and other relays
    """

    counter = 0
    logger = current_app.logger
    mutex = Lock()

    def __init__(
        self,
        id: str,
        name: str,
        board: int,
        relay: int,
        requires: list[Dependency] = None,
        #  is_dependency: bool = False
    ) -> None:
        self.id = id
        self.name = name
        self.board = board
        self.relay = relay
        self.requires = requires
        self.timer = Timmy(self.name)
        Relay.logger.debug(" ".join(["Relay", str(self.name), "initialized"]))

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
        if self.counter == 0:
            if self.requires is not None:
                for dep in self.requires:
                    dep.relay.on()
                    sleep(dep.spin_up)
            relayON(self.board, self.relay)
        #  don't increment if the timer is changed while active
        if interval is None or self.timer.is_set() is False:
            self.mutex.acquire()
            self.counter += 1
            self.mutex.release()
        if interval is not None:
            self.timer.set(
                interval, self.off if callback is None else callback, args)
        Relay.logger.info(" ".join(["Relay", str(self.name), "on"]))

    def off(self) -> None:
        """
        Decrement the counter
        Turns off the relay if the counter is reduced to zero
        """
        self.mutex.acquire()
        self.counter -= 1
        self.mutex.release()
        if self.counter == 0:
            if self.requires is not None:
                for dep in self.requires:
                    dep.relay.off()
            relayOFF(self.board, self.relay)
            self.timer.clear()
        Relay.logger.info(" ".join(["Relay", str(self.name), "off"]))
