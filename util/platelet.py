"""
Controller helper classes for Pi-Plates RelayPlate
"""
from datetime import timedelta
from test.plates import relayOFF, relayON, relaySTATE
from typing import Any, Callable

from flask import current_app

from util.timmy import Timmy

# from piplates.RELAYplate import relayOFF, relayON, relaySTATE


class Zone:
    """
    Helper class that couples relays to timers
    """

    logger = current_app.logger

    def __init__(self, name: str, board: int, relay: int) -> None:
        self.name = name
        self.board = board
        self.relay = relay
        self.timer = Timmy(self.name)
        Zone.logger.debug(" ".join(["Zone", str(self.name), "initialized"]))

    def on(
        self,
        interval: timedelta,
        callback: Callable[[...], Any] = None,
        args: list[str] = None,
    ) -> None:
        """
        Turns on the zone
        """
        relayON(self.board, self.relay)
        self.timer.set(interval, self.off if callback is None else callback, args)
        Zone.logger.info(" ".join(["Zone", str(self.name), "on"]))

    def off(self) -> None:
        """
        Turns off the zone
        """
        relayOFF(self.board, self.relay)
        self.timer.clear()
        Zone.logger.info(" ".join(["Zone", str(self.name), "off"]))


class Platelet:
    """
    Static controller class for manipulating Zone objects
    """

    zones = [Zone(x + 1, y, z) for x, (y, z) in enumerate(current_app.config["ZONES"])]
    boards = {x[0] for x in current_app.config["ZONES"]}
    num_zones = current_app.config["NUM_ZONES"]
    max_zones = current_app.config["MAX_ZONES"]
    max_minutes = current_app.config["MAX_TIME"]
    pump_zone = (
        None
        if current_app.config["PUMP_ZONE"] is None
        else Zone(
            "Pump",
            current_app.config["PUMP_ZONE"][0],
            current_app.config["PUMP_ZONE"][1],
        )
    )

    logger = current_app.logger

    @staticmethod
    def get_state():
        """
        Method that determines which of the zone relays are on, if any.
        Returns a list that can be passed as an argument to the index page
        """
        # Get state bits for each board
        states = {x: relaySTATE(x) for x in Platelet.boards}
        # Check bitwise each state against all zones for that board
        active = [
            zone.name
            for zone in Platelet.zones
            if (states[zone.board] >> (zone.relay - 1)) % 2
        ]
        # Check the pump state, if applicable and only
        # append pump when no other zones are active
        if Platelet.pump_zone is not None and active == []:
            if (states[Platelet.pump_zone.board] >> (Platelet.pump_zone.relay - 1)) % 2:
                active.append("Pump")
        Platelet.logger.debug(
            " ".join(
                ["Returned getState() with active zones"] + [str(x) for x in active]
            )
        )
        return active

    @staticmethod
    def pump_on(interval: timedelta) -> None:
        """
        Turn on the pump, if it is present, for a given timedelta
        """
        if Platelet.pump_zone is not None:
            Platelet.pump_zone.on(interval)
            Platelet.logger.info(
                " ".join(
                    [
                        "Pump was turned on for",
                        str(interval),
                    ]
                )
            )
        else:
            Platelet.logger.debug(
                "Call to pumpOn() but pump NOT turned on; no pump zone set"
            )

    @staticmethod
    def pump_off() -> None:
        """
        Turn off the pump, if present
        """
        if Platelet.pump_zone is not None:
            Platelet.pump_zone.off()
            Platelet.logger.info("Pump was turned off")

    @staticmethod
    def zone_on(zone_id: int, interval: timedelta) -> None:
        """
        Turn a relay specified by id on for a given timedelta, but only if the number
        of active relays is fewer than what is specified in the configuration
        """
        if len(Platelet.get_state()) < Platelet.max_zones:
            Platelet.pump_on(interval)
            Platelet.zones[int(zone_id) - 1].on(interval)
            Platelet.logger.info(
                " ".join(
                    [
                        "Zone",
                        str(zone_id),
                        "was turned on for",
                        str(interval),
                    ]
                )
            )

    @staticmethod
    def zone_off(zone_id: int) -> None:
        """
        Method that turns a zone off, given its id
        """
        if len(Platelet.get_state()) == 1:
            Platelet.pump_off()
        Platelet.zones[int(zone_id) - 1].off()
        Platelet.logger.info(" ".join(["Zone", str(zone_id), "was turned off"]))

    @staticmethod
    def all_off() -> None:
        """
        Method that turns everything off
        """
        for zone in Platelet.zones:
            zone.off()
        Platelet.pump_off()
