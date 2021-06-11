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

# Configure logging format and verbosity

# Declare the number of sprinkler zones
NUM_ZONES = 5
# Declare the zone number for the master switch
MASTER_ZONE = 7
# A list to hold a timer object
zone_timer = None

# A function for turning a zone on
def zoneOn(zone: int):
    state = relaySTATE(0)
    # Turn on the argument zone only if there isn't
    # already another zone turned on
    if state == 0:
        # It should be safe to turn on the master switch
        # even when it is already switched on
        relayON(0,MASTER_ZONE)
        relayON(0,zone)

# A function for turning a zone off (possibly early)
def zoneOff(zone: int):
    relayOFF(0,MASTER_ZONE)
    relayOFF(0,zone)


@app.route('/')
def index():
    state = relaySTATE(0)
    # Check each bit of state and comp a list of bools
    # which represents whether each zone is on or off
    active = [ x for x in range(0,NUM_ZONES) if (state >> x) % 2 ]
    return render_template('zone.html', num_zones=NUM_ZONES, active=active)

@app.route('/time/<int:zone>/')
def time(zone):
    return render_template('time.html', zone=zone)

@app.route('/confirm/<int:zone>/<int:time>/')
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
    zone_timer = Timer(60.0 * time, zoneOff(zone))
    return redirect(url_for('.index'))
