"""
Controller helper classes for Pi-Plates RelayPlate
"""
# from piplates.RELAYplate import relaySTATE, relayON, relayOFF
from test.plates import relayOFF, relayON, relaySTATE
from util.timmy import Timmy

from flask import current_app


class Zone:
    """
    Helper class that couples relays to timers
    """

    logger = current_app.logger

    def __init__(self, name, board, relay):
        self.name = name
        self.board = board
        self.relay = relay
        self.timer = Timmy(self.name)
        Zone.logger.debug(" ".join(["Zone", str(self.name), "initialized"]))

    def on(self, interval, callback=None, args=None):
        """
        Turns on the zone
        """
        relayON(self.board, self.relay)
        self.timer.set(interval, self.off if callback is None else callback, args)
        Zone.logger.debug(" ".join(["Zone", str(self.name), "on"]))

    def off(self):
        """
        Turns off the zone
        """
        relayOFF(self.board, self.relay)
        self.timer.clear()
        Zone.logger.debug(" ".join(["Zone", str(self.name), "off"]))


class Platelet:
    """
    Static controller class for manipulating Zone objects
    """

    # A list of zone objects, each having a timer object
    zones = [Zone(x + 1, y, z) for x, (y, z) in enumerate(current_app.config["ZONES"])]
    # Persist a list of board addresses
    boards = {x[0] for x in current_app.config["ZONES"]}
    # Persist the number of zones
    num_zones = current_app.config["NUM_ZONES"]
    # Persist the pump zone
    pump_zone = (
        None
        if current_app.config["PUMP_ZONE"] is None
        else Zone(
            "Pump",
            current_app.config["PUMP_ZONE"][0],
            current_app.config["PUMP_ZONE"][1],
        )
    )
    # Persist the max number of concurrent zones
    max_zones = current_app.config["MAX_ZONES"]
    # Persist the logger object
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
    def pump_on(interval: int):
        """
        Method that turns on the pump, if it is present, for a given time
        interval in minutes
        """
        if Platelet.pump_zone is not None:
            Platelet.pump_zone.on(interval)
            Platelet.logger.info(
                " ".join(
                    [
                        "Pump was turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                    ]
                )
            )
        else:
            Platelet.logger.debug(
                "Call to pumpOn() but pump NOT turned on; no pump zone set"
            )

    @staticmethod
    def pump_off():
        """
        Method that turns off the pump, if present
        """
        if Platelet.pump_zone is not None:
            Platelet.pump_zone.off()
            Platelet.logger.info("Pump was turned off")

    @staticmethod
    def zone_on(zone_id: int, interval: int):
        """
        Method that turns a zone specified by id on for a given time interval
        in minutes
        """
        # Turn on the argument zone only if there isn't
        # already another zone or sequence turned on
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
                        "minute." if interval == 1 else "minutes.",
                    ]
                )
            )

    @staticmethod
    def zone_off(zone_id: int):
        """
        Method that turns a zone off, given its id
        """
        if len(Platelet.get_state()) == 1:
            Platelet.pump_off()
        Platelet.zones[int(zone_id) - 1].off()
        Platelet.logger.info(" ".join(["Zone", str(zone_id), "was turned off"]))

    @staticmethod
    def all_off():
        """
        Method that turns everything off
        """
        for zone in Platelet.zones:
            zone.off()
        Platelet.pump_off()