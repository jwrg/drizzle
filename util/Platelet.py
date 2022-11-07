from time import time as now
from threading import Timer
from piplates.RELAYplate import relaySTATE, relayON, relayOFF
#from test.plates import relaySTATE, relayON, relayOFF

from flask import current_app

# Controller helper classes for Pi-Plates RelayPlate
class Zone:
    logger = current_app.logger

    def __init__(self, name, board, relay):
        self.name = name
        self.board = board
        self.relay = relay
        self.timer = self.Timer(self.name)
        Zone.logger.debug(" ".join(["Zone", str(self.name), "initialized"]))

    def on(self, time, callback=None, args=[]):
        relayON(self.board, self.relay)
        self.timer.set(time, self.off if callback == None else callback, args)
        Zone.logger.debug(" ".join(["Zone", str(self.name), "on"]))

    def off(self):
        relayOFF(self.board, self.relay)
        self.timer.clear()
        Zone.logger.debug(" ".join(["Zone", str(self.name), "off"]))

    class Timer:
        def __init__(self, name):
            self.name = name
            self.timer = None
            # Start time in seconds from the epoch
            self.start = 0
            # Interval time in minutes
            self.interval = 0

        # Function for getting remaining timer interval
        def remaining(self):
            if self.timer is not None:
                return ((self.start + (self.interval * 60)) - now()) / 60
            else:
                return 0

        # Functions for setting and clearing timers
        def set(self, time, callback, args):
            if time > self.remaining():
                if self.timer is not None:
                    self.timer.cancel()
                    self.timer = None
                    Zone.logger.debug(" ".join(["Timer", str(self.name), "extended."]))
                self.interval = time
                self.start = now()
                self.timer = Timer(60.0 * time, callback, args)
                self.timer.start()
                Zone.logger.debug(
                    " ".join(
                        [
                            "Timer",
                            str(self.name),
                            "set for",
                            str(time),
                            "minute." if time == 1 else "minutes.",
                        ]
                    )
                )
            else:
                Zone.logger.debug(
                    " ".join(
                        [
                            "Timer",
                            str(self.name),
                            "not set! Arg",
                            str(time),
                            "ends before currently set timer",
                        ]
                    )
                )

        def clear(self):
            if self.timer is not None:
                self.interval = 0
                self.start = 0
                self.timer.cancel()
                self.timer = None
                Zone.logger.debug(" ".join(["Timer", str(self.name), "cleared."]))


class Platelet:
    # A list of zone objects, each having a timer object
    zones = [Zone(x + 1, y, z) for x, (y, z) in enumerate(current_app.config["ZONES"])]
    # Persist a list of board addresses
    boards = {x[0] for x in current_app.config["ZONES"]}
    # Persist the number of zones
    num_zones = current_app.config["NUM_ZONES"]
    # Persist the pump zone
    pump_zone = (
        None
        if current_app.config["PUMP_ZONE"] == None
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

    # A function for determining which of the zone
    # relays are on, if any.  Returns a list that can
    # be passed to the index page
    def getState():
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

    # Functions for turning on/off the pump, when applicable
    def pumpOn(time: int):
        if Platelet.pump_zone is not None:
            Platelet.pump_zone.on(time)
            Platelet.logger.info(
                " ".join(
                    [
                        "Pump was turned on for",
                        str(time),
                        "minute." if time == 1 else "minutes.",
                    ]
                )
            )
        else:
            Platelet.logger.debug(
                "Call to pumpOn() but pump NOT turned on; no pump zone set"
            )

    def pumpOff():
        if Platelet.pump_zone is not None:
            Platelet.pump_zone.off()
            Platelet.logger.info("Pump was turned off")

    # A function for turning a zone on (argument not zero-indexed)
    def zoneOn(zone: int, time: int):
        # Turn on the argument zone only if there isn't
        # already another zone or sequence turned on
        if len(Platelet.getState()) < Platelet.max_zones:
            Platelet.pumpOn(time)
            Platelet.zones[int(zone) - 1].on(time)
            Platelet.logger.info(
                " ".join(
                    [
                        "Zone",
                        str(zone),
                        "was turned on for",
                        str(time),
                        "minute." if time == 1 else "minutes.",
                    ]
                )
            )

    # A function for turning a zone off (argument not zero-indexed)
    def zoneOff(zone: int):
        if len(Platelet.getState()) == 1:
            Platelet.pumpOff()
        Platelet.zones[int(zone) - 1].off()
        Platelet.logger.info(" ".join(["Zone", str(zone), "was turned off"]))

    # A function to turn everything off
    def allOff():
        for zone in Platelet.zones:
            zone.off()
        Platelet.pumpOff()
