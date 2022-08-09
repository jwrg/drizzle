from threading import Timer
from json import dump, load
from re import match
from time import strftime
#from piplates.RELAYplate import relaySTATE, relayON, relayOFF
from flask import Flask, render_template, redirect, request, url_for
app = Flask(__name__)

# NB That this app makes no assumptions regarding
# the specific relays the user wishes to utilize
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

# A list of references to Timer objects; this is
# initialized as a list of None values
# NB that zone 0 is reserved for the pump
TIMERS = [ None for x in range(0, NUM_ZONES + 1) ]

# The application port on which the app listens
APP_PORT = 8080

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
    if PUMP_ZONE is not None and active == []:
        if (STATES[PUMP_ZONE[0]] >> (PUMP_ZONE[1] - 1)) % 2:
            active.append("Pump")
    return active

# Functions for turning on/off the pump, when applicable
def pumpOn():
    if PUMP_ZONE is not None and len(getState()) < MAX_ZONES:
        relayON(PUMP_ZONE[0], PUMP_ZONE[1])
def pumpOff():
    if PUMP_ZONE is not None:
        relayOFF(PUMP_ZONE[0], PUMP_ZONE[1])

# A function for turning a zone on (argument not zero-indexed)
def zoneOn(zone: int):
    # Turn on the argument zone only if there isn't
    # already another zone turned on
    if len(getState()) < MAX_ZONES:
        pumpOn()
        relayON(ZONES[zone - 1][0], ZONES[zone - 1][1])

# A function for turning a zone off (argument not zero-indexed)
def zoneOff(zone: int):
    # Turn off pump only when there is no active pump timer
    if len(getState()) == 1 and TIMERS[0] is None:
        pumpOff()
    relayOFF(ZONES[zone - 1][0], ZONES[zone - 1][1])

# A function for reading the local sequences json file.
# Returns a dict, since the top-level type is object
def getSequences():
    with open("sequences.json", "r") as file:
        return load(file)

def putSequences(data):
    with open("sequences.json", "w") as file:
        return dump(data, file, sort_keys=True)


# Routes for the homepage
@app.route('/')
def index():
    return render_template('zone.html', num_zones=NUM_ZONES, pump=PUMP_ZONE, active=getState())

# Routes for the zones page
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
        if TIMERS[0]:
            TIMERS[0].cancel()
            TIMERS[0] = None;
    else:
        zoneOff(zone)
        if TIMERS[zone]:
            TIMERS[zone].cancel()
            TIMERS[zone] = None;
    return redirect(url_for('.index'))

@app.route('/enable/<int:zone>/<int:time>/')
def enable(zone, time):
    if time <= MAX_TIME:
        if zone == 0:
            pumpOn()
            TIMERS[0] = Timer(60.0 * time, pumpOff)
            TIMERS[0].start()
        else:
            zoneOn(zone)
            TIMERS[zone] = Timer(60.0 * time, zoneOff, [zone])
            TIMERS[zone].start()
    return redirect(url_for('.index'))

# Routes for the sequences page
@app.route('/sequences/')
def sequences():
    return render_template('sequence.html', sequences=getSequences())

@app.route('/sequences/new/')
def newSequence():
    return render_template('edit_sequence.html',\
            sequences={str(max([int(x) for x in getSequences().keys()]) + 1):\
            {'name': '', 'description': '',\
            'created': strftime('%Y-%m-%dT%H:%M:%S.999Z'),\
            'modified': '',\
            'sequence': [[1,1]]}},\
            id=str(max([int(x) for x in getSequences().keys()]) + 1),\
            num_zones=NUM_ZONES)

@app.route('/sequences/edit/<int:id>/', methods=('GET', 'POST'))
def editSequence(id):
    if request.method == 'POST':
        fields = ['name', 'description', 'created']
        resultant = {}
        for field in fields:
            if request.form[field] == '':
                resultant[field] = field
            else:
                resultant[field] = request.form[field]
        resultant['modified'] = strftime('%Y-%m-%dT%H:%M:%S.999Z')
        resultant['sequence'] = [list(x) for x in zip(\
                [int(request.form.get(y)) for y in \
                [z for z in [*request.form.keys()] \
                if match('select-*', z)]],\
                [int(request.form.get(y)) for y in \
                [z for z in [*request.form.keys()] \
                if match('time-*', z)]]\
                )]
        sequences = getSequences()
        sequences.update({str(id): resultant})
        putSequences(sequences)
        return redirect(url_for('sequences'))
    return render_template('edit_sequence.html', sequences=getSequences(), id=str(id), num_zones=NUM_ZONES)

@app.route('/sequences/delete/<int:id>/')
def deleteSequence(id):
    sequences = getSequences()
    sequences.pop(str(id))
    putSequences(sequences)
    return redirect(url_for('sequences'))

if __name__ == "__main__":
    import bjoern
    bjoern.run(app, "0.0.0.0", APP_PORT)
