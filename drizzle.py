import time
import logging
from threading import Timer
import piplates.RELAYplate as plate
from flask import Flask
from flask import render_template
from flask import redirect
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

@app.route('/time/<int:zone>/')
def time(zone):
    return render_template('time.html', zone=zone)

@app.route('/confirm/<int:zone>/<int:time>/<bool:enable>/')
def confirm(zone, time):
    return render_template('confirm.html', zone=zone, time=time)

@app.route('/disable/<int:zone>/')
def disable(zone):
    # Turn off the requested zone
    zoneOff(zone)
    return redirect(url_for('.index'))

@app.route('/enable/<int:zone>/<int:time>/')
def enable(zone, time):
    # Turn on the requested zone
    zoneOn(zone)
    # Create a timer object to turn off the zone
    # after the specified number of minutes
    zone_timers[zone] = Timer(60.0 * time, zoneOff(zone))
    return redirect(url_for('.index'))
