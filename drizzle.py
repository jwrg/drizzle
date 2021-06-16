from threading import Timer
from piplates.RELAYplate import relaySTATE, relayON, relayOFF
from flask import Flask, render_template, redirect, url_for
app = Flask(__name__)

# NB That this app makes no assumptions regarding
# the specific relays the user whiches to utilize
# for each zone.  To this extent, the user is expected
# to provide not only the number of zones, but also
# the board and relay id number for each zone, given
# in order.  The default example is for five zones,
# requiring only one relay board and with an extra
# relay used for powering a pump.

# The user can declare how many zones should be on
# at once, and can also turn the pump on by itself; 
# the app counts and displays this as another zone.

# Declare the number of sprinkler zones (not including pump)
NUM_ZONES = 5
# Declare the number of concurrently active zones allowed
MAX_ZONES = 1
# Declare the max time for which a zone may be active
MAX_TIME = 31
# Declare the address (board, relay) for each zone
# NB that the interface starts counting zones at one
# but this tuple is zero-indexed.  Relays on the
# boards start at K1 and so the first relay is relay
# 1, since there is no K0.  Not confusing at all.
ZONES = (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)
# Declare the zone number for the pump switch (to
# denote that no pump is used, give the value as None)
PUMP_ZONE = (0, 7)

# A function for determining which of the zone
# relays are on, if any.  Returns a list that can
# be passed to the index page
def getState():
    # Get a list of board addresses found in ZONES
    BOARDS = list({x[0] for x in ZONES})
    BOARDS.sort()
    # Get a state for each board
    STATES = {x: relaySTATE(x) for x in BOARDS}
    # Check each state against all zones for that board
    active = [x for x in range(0, NUM_ZONES) if (STATES[ZONES[x][0]] >> (ZONES[x][1] - 1)) % 2]
    # Check the pump state, if applicable and only check
    # when no other zones are active
    if PUMP_ZONE != None and active == []:
        if (STATES[PUMP_ZONE[0]] >> (PUMP_ZONE[1] - 1)) % 2:
            active.append("Pump")
    return active

# Functions for turning on/off the pump, when applicable
def pumpOn():
    if PUMP_ZONE != None and len(state) < MAX_ZONES:
        relayON(PUMP_ZONE[0], PUMP_ZONE[1])
def pumpOff():
    if PUMP_ZONE != None:
        relayOFF(PUMP_ZONE[0], PUMP_ZONE[1])

# A function for turning a zone on (argument not zero-indexed)
def zoneOn(zone: int):
    state = getState()
    # Turn on the argument zone only if there isn't
    # already another zone turned on
    if len(state) < MAX_ZONES:
        pumpOn()
        relayON(ZONES[zone - 1][0], ZONES[zone - 1][1])

# A function for turning a zone off (argument not zero-indexed)
def zoneOff(zone: int):
    pumpOff()
    relayOFF(ZONES[zone - 1][0], ZONES[zone - 1][1])


@app.route('/')
def index():
    return render_template('zone.html', num_zones=NUM_ZONES, pump=PUMP_ZONE, active=getState())

@app.route('/time/<int:zone>/')
def time(zone):
    return render_template('time.html', zone=zone)

@app.route('/confirm/<int:zone>/<int:time>/')
def confirm(zone, time):
    return render_template('confirm.html', zone=zone, time=time)

@app.route('/disable/<int:zone>/')
def disable(zone):
    if zone == 0:
        pumpOff()
    else:
        zoneOff(zone)
    return redirect(url_for('.index'))

@app.route('/enable/<int:zone>/<int:time>/')
def enable(zone, time):
    if time <= MAX_TIME:
        if zone == 0:
            pumpOn()
            pump_timer = Timer(60.0 * time, pumpOff)
            pump_timer.start()
        else:
            zoneOn(zone)
            zone_timer = Timer(60.0 * time, zoneOff, [zone])
            zone_timer.start()
    return redirect(url_for('.index'))

if __name__ == "__main__":
    import bjoern
    bjoern.run(app, "0.0.0.0", 8080)
