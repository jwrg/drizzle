import threading
import time
import logging
import piplates.RELAYplate as plate
from flask import Flask
from flask import render_template
app = Flask(__name__)

# Configure logging format and verbosity

# Declare the number of sprinkler zones
NUM_ZONES = 5
# Declare the zone number for the master switch
MASTER_ZONE = 7
# A list to hold timer objects
zone_timers = []

# A function for turning a zone on
def zoneOn(zone: int):
    # It should be safe to turn on the master switch
    # even when it is already switched on
    plate.relayON(0,MASTER_ZONE)
    # Turn on the argument zone
    plate.relayON(0,zone)

# A function for turning a zone off (possibly early)
def zoneOff(zone: int):
    state = plate.relaySTATE(0)
    # If the state is master plus argument zone
    if state == 1 << (MASTER_ZONE - 1) + 1 << (zone - 1):
        # Then turn off the master zone
        plate.relayOFF(0,MASTER_ZONE)
    # Regardless, we wish to turn off the arg zone
    plate.relayOFF(0,zone)


@app.route('/')
def index():
    state = plate.relaySTATE(0)
    # Check each bit of state and comp a list of bools
    # which represents whether each zone is on or off
    active = [ x for x in range(0,NUM_ZONES) if (state >> x) % 2 ]
    return render_template('zone.html', num_zones=NUM_ZONES, active=active)

@app.route('/time/<int:id>/')
def time(id):
    return render_template('time.html', zone=id)

@app.route('/zone/<int:id>/<int:time>/')
def zone(id, time):
    return 'Turning on zone %d for %d minutes.' % (id, time)
