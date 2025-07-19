"""
Controller helper classes for Pi-Plates RelayPlate
"""
from __future__ import annotations
from datetime import timedelta
from re import match

from flask import current_app

from util.relay import Relay, Dependency


class Platelet:
    """
    Static controller class for manipulating Relay objects
    """

    class Platter:
        """
        Static class for loading up relays from app config
        """

        @staticmethod
        def get_relays():
            levels = len([x for x in current_app.config.keys()
                         if match("RELAYS_.*", x)])
            objects = {
                name: Relay(name, board, relay)
                for x, (name, board, relay)
                in enumerate(current_app.config["RELAYS"])
            }
            for x in range(levels):
                objects = objects | {
                    name: Relay(name, board, relay, [
                        Dependency(objects[dep], spin_up)
                        for (dep, spin_up) in requires
                    ]
                    )
                    for x, (name, board, relay, requires)
                    in enumerate(current_app.config["RELAYS_" + str(x + 1)])
                }
            return objects

    relays = Platter.get_relays()
    boards = {y.board for x, y in relays.items()}
    num_relays = len(relays)
    max_relays = current_app.config["MAX_RELAYS"]
    min_minutes = current_app.config["MIN_TIME"]
    max_minutes = current_app.config["MAX_TIME"]
    default_minutes = current_app.config["DEFAULT_TIME"]
    logger = current_app.logger

    @staticmethod
    def get_state():
        """
        Method that determines which of the relays are on, if any.
        Returns a dict that can be passed as an argument to the index page
        """
        active = {
            relay.name: relay.timer.remaining().total_seconds()
            for name, relay in Platelet.relays.items()
            if relay.timer.remaining().total_seconds() > 0
        }
        Platelet.logger.debug(
            " ".join(
                ["Returned getState() with active relays"] + [str(x)
                                                              for x in active]
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
                        str(relay_id),
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
            " ".join(["Relay", str(relay_id), "was turned off"]))

    @staticmethod
    def all_off() -> None:
        """
        Method that turns everything off
        """
        for name, relay in Platelet.relays.items():
            relay.off()
