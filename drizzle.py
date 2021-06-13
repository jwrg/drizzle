import time
import logging
from threading import Timer
from piplates.RELAYplate import relaySTATE
from piplates.RELAYplate import relayON
from piplates.RELAYplate import relayOFF
from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
app = Flask(__name__)

# NB That this app makes no assumptions regarding
# the specific relays the user whiches to utilize
# for each zone.  To this extent, the user is expected
# to provide not only the number of zones, but also
# the board and relay id number for each zone, given
# in order.  The default example is for five zones,
# requiring only one relay board and with an extra
# relay used for powering a pump.

# Declare the number of sprinkler zones
NUM_ZONES = 5
# Declare the address (board, relay) for each zone
# NB that the interface starts counting zones at one
# but this tuple is zero-indexed
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
    STATES = [relaySTATE(x) for x in BOARDS]
    # Check each state against all zones for that board
    active = [x for x in range(0, NUM_ZONES) if (STATES[ZONES[x][0]] >> (ZONES[x][1] - 1)) % 2]
    # Concatenate and return sequential zone list of bools
    return active

# Functions for turning on/off the pump, when applicable
def pumpOn():
    if PUMP_ZONE != None:
        relayON(PUMP_ZONE[0], PUMP_ZONE[1])
def pumpOff():
    if PUMP_ZONE != None:
        relayOFF(PUMP_ZONE[0], PUMP_ZONE[1])

# A function for turning a zone on (argument not zero-indexed)
def zoneOn(zone: int):
    state = getState()
    # Turn on the argument zone only if there isn't
    # already another zone turned on
    if state == []:
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
    zoneOff(zone)
    return redirect(url_for('.index'))

@app.route('/enable/<int:zone>/<int:time>/')
def enable(zone, time):
    zoneOn(zone)
    # Create a timer object to turn off the zone
    # after the specified number of minutes
    zone_timer = Timer(60.0 * time, zoneOff, [zone])
    zone_timer.start()
    return redirect(url_for('.index'))

if __name__ == "__main__":
    import bjoern
    bjoern.run(app, "0.0.0.0", 8080)
