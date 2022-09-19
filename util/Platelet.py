from threading import Timer
from piplates.RELAYplate import relaySTATE, relayON, relayOFF
#from test.plates import relaySTATE, relayON, relayOFF

from flask import current_app

# Controller helper class for Pi-Plates RelayPlate
class Platelet:
    # A list of references to Timer objects; this is
    # initialized as a list of None values
    # NB that zone 0 is reserved for the pump
    timers = [ None for x in range(0, current_app.config['NUM_ZONES'] + 1) ]
    # Persist a list of zones
    zones = current_app.config['ZONES']
    # Get a list of board addresses found in app.config['ZONES']
    boards = list({x[0] for x in current_app.config['ZONES']})
    # Persist the number of zones
    num_zones = current_app.config['NUM_ZONES']
    # Persist the pump zone
    pump_zone = current_app.config['PUMP_ZONE']
    # Persist the max number of concurrent zones
    max_zones = current_app.config['MAX_ZONES']
    # Persist the logger object
    logger = current_app.logger

    # A function for determining which of the zone
    # relays are on, if any.  Returns a list that can
    # be passed to the index page
    def getState():
        # Get a state for each board
        states = {x: relaySTATE(x) for x in Platelet.boards}
        # Check each state against all zones for that board
        active = [ 
                x + 1 for x 
                in range(0, Platelet.num_zones) 
                if (states[Platelet.zones[x][0]] >> (Platelet.zones[x][1] - 1)) % 2
                ]
        # Check the pump state, if applicable and only check
        # when no other zones are active
        if Platelet.pump_zone is not None and active == []:
            if (states[Platelet.pump_zone[0]] >> (Platelet.pump_zone[1] - 1)) % 2:
                active.append('Pump')
        Platelet.logger.debug(' '.join(['Returned getState() with active zones'] + [str(x) for x in active]))
        return active

    # Functions for turning on/off the pump, when applicable
    def pumpOn():
        if Platelet.pump_zone is not None and len(Platelet.getState()) < Platelet.max_zones:
            relayON(Platelet.pump_zone[0], Platelet.pump_zone[1])
            Platelet.logger.info('Pump was turned on')
        else:
            Platelet.logger.debug('Call to pumpOn() but pump NOT turned on')
    def pumpOff():
        if Platelet.pump_zone is not None:
            relayOFF(Platelet.pump_zone[0], Platelet.pump_zone[1])
            Platelet.logger.info('Pump was turned off')

    # A function for turning a zone on (argument not zero-indexed)
    def zoneOn(zone: int):
        # Turn on the argument zone only if there isn't
        # already another zone or sequence turned on
        if len(Platelet.getState()) < Platelet.max_zones:
            Platelet.pumpOn()
            relayON(Platelet.zones[zone - 1][0], Platelet.zones[zone - 1][1])
            Platelet.logger.info(' '.join(['Zone', str(zone), 'was turned on']))

    # A function for turning a zone off (argument not zero-indexed)
    def zoneOff(zone: int):
        # Turn off pump only when there is no active pump timer
        if len(Platelet.getState()) == 1 and Platelet.timers[0] is None:
            Platelet.pumpOff()
        relayOFF(Platelet.zones[zone - 1][0], Platelet.zones[zone - 1][1])
        Platelet.logger.info(' '.join(['Zone', str(zone), 'was turned off']))
