"""
Controller helper classes for Pi-Plates RelayPlate
"""
from __future__ import annotations
from datetime import timedelta
from re import match

from flask import current_app

from util.jsonny import Jsonny
from util.relay import Relay, Dependency


class Platelet:
    """
    Static controller class for manipulating Relay objects
    """

    class Platter:
        """
        Static class for loading up relays from app config
        """
        def init_relays(json) -> dict[str, Relay]:
            levels = len([x for x in json.keys()
                         if match("RELAYS_.*", x)])
            objects = {
                id: Relay(id, name, board, relay)
                for x, (id, name, board, relay)
                in enumerate(json["RELAYS"])
            }
            for x in range(levels):
                objects = objects | {
                    id: Relay(id, name, board, relay, [
                        Dependency(objects[dep], spin_up)
                        for (dep, spin_up) in requires
                    ]
                    )
                    for x, (id, name, board, relay, requires)
                    in enumerate(json["RELAYS_" + str(x + 1)])
                }
            return objects

    default_filename = "relays"
    jsonny = Jsonny(default_filename)
    logger = current_app.logger

    relays = Platter.init_relays(jsonny.json)
    boards = {relay.board for relay in relays.values()}
    num_relays = len(relays)
    max_relays = jsonny.json["MAX_RELAYS"]
    min_minutes = jsonny.json["MIN_TIME"]
    max_minutes = jsonny.json["MAX_TIME"]
    default_minutes = jsonny.json["DEFAULT_TIME"]

    @staticmethod
    def get_state() -> dict:
        """
        Method that determines which of the relays are on, if any.
        Returns a dict that can be passed as an argument to the index page
        """
        active = {
            id: relay.timer.remaining().total_seconds()
            for id, relay in Platelet.relays.items()
            if relay.timer.is_set()
        }
        Platelet.logger.debug(
            " ".join(
                [
                    "Returned get_state() with",
                    "no relays active" if len(active) == 0 else "active relays"
                ] + [Platelet.relays[x].name for x in active]
            )
        )
        return active

    @staticmethod
    def relay_on(relay_id: str, interval: timedelta) -> None:
        """
        Turn a relay specified by id on for a given timedelta, but only if the number
        of active relays is fewer than what is specified in the configuration
        """
        if len(Platelet.get_state()) < Platelet.max_relays:
            Platelet.relays[relay_id].on(interval)
            Platelet.logger.info(
                " ".join(
                    [
                        "Relay",
                        Platelet.relays[relay_id].name,
                        "was turned on for",
                        str(interval),
                    ]
                )
            )

    @staticmethod
    def relay_off(relay_id: str) -> None:
        """
        Method that turns a relay off, given its id
        """
        Platelet.relays[relay_id].off()
        Platelet.logger.info(
            " ".join(
                [
                    "Relay",
                    Platelet.relays[relay_id].name,
                    "was turned off"
                ]
            )
        )

    @staticmethod
    def all_off() -> None:
        """
        Method that turns everything off
        """
        for relay in Platelet.relays.values():
            relay.off()
