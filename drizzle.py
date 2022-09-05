from threading import Timer
from json import dump, load
from re import match
from time import strftime
from piplates.RELAYplate import relaySTATE, relayON, relayOFF
#from test.plates import relaySTATE, relayON, relayOFF
from flask import Flask, flash, render_template, redirect, request, url_for
app = Flask(__name__)
app.config.from_json('config.json')
app.logger.setLevel(app.config['LOG_LEVEL'])

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
# Declare the number of concurrently active zones allowed
# Declare the max time for which a zone may be active
# Declare the address (board, relay) for each zone
# NB that the interface starts counting zones at one
# but this tuple is zero-indexed.  Relays on the
# boards start at K1 and so the first relay is relay
# 1, since there is no K0.  Not confusing at all.
# Declare the zone number for the pump switch (to
# denote that no pump is used, give the value as None)

# Controller helper class for Pi-Plates RelayPlate
class Platelet:
    # A list of references to Timer objects; this is
    # initialized as a list of None values
    # NB that zone 0 is reserved for the pump
    timers = [ None for x in range(0, app.config['NUM_ZONES'] + 1) ]

    # A function for determining which of the zone
    # relays are on, if any.  Returns a list that can
    # be passed to the index page
    def getState():
        # Get a list of board addresses found in app.config['ZONES']
        boards = list({x[0] for x in app.config['ZONES']})
        boards.sort()
        # Get a state for each board
        states = {x: relaySTATE(x) for x in boards}
        # Check each state against all zones for that board
        active = [x for x in range(1, app.config['NUM_ZONES'] + 1) if (states[app.config['ZONES'][x - 1][0]] >> (app.config['ZONES'][x - 1][1] - 1)) % 2]
        # Check the pump state, if applicable and only check
        # when no other zones are active
        if app.config['PUMP_ZONE'] is not None and active == []:
            if (states[app.config['PUMP_ZONE'][0]] >> (app.config['PUMP_ZONE'][1] - 1)) % 2:
                active.append('Pump')
        app.logger.debug(' '.join(['Returned getState() with active zones'] + [str(x) for x in active]))
        return active

    # Functions for turning on/off the pump, when applicable
    def pumpOn():
        if app.config['PUMP_ZONE'] is not None and len(Platelet.getState()) < app.config['MAX_ZONES']:
            relayON(app.config['PUMP_ZONE'][0], app.config['PUMP_ZONE'][1])
            app.logger.info('Pump was turned on')
        else:
            app.logger.debug('Call to pumpOn() but pump NOT turned on')
    def pumpOff():
        if app.config['PUMP_ZONE'] is not None:
            relayOFF(app.config['PUMP_ZONE'][0], app.config['PUMP_ZONE'][1])
            app.logger.info('Pump was turned off')

    # A function for turning a zone on (argument not zero-indexed)
    def zoneOn(zone: int):
        # Turn on the argument zone only if there isn't
        # already another zone or sequence turned on
        if len(Platelet.getState()) < app.config['MAX_ZONES']:
            Platelet.pumpOn()
            relayON(app.config['ZONES'][zone - 1][0], app.config['ZONES'][zone - 1][1])
            app.logger.info(' '.join(['Zone', str(zone), 'was turned on']))

    # A function for turning a zone off (argument not zero-indexed)
    def zoneOff(zone: int):
        # Turn off pump only when there is no active pump timer
        if len(Platelet.getState()) == 1 and Platelet.timers[0] is None:
            Platelet.pumpOff()
        relayOFF(app.config['ZONES'][zone - 1][0], app.config['ZONES'][zone - 1][1])
        app.logger.info(' '.join(['Zone', str(zone), 'was turned off']))

# Class for running and handling sequences
class Sequencer:
    # An integer for holding the id of the currently running
    # sequence.  None denotes no sequence is currently active
    # NB this obviously implies that only one sequence may
    # be active at a time
    sequence = None

    # A reference to a Timer object; this is initialized as
    # None, which denotes that there is no active sequence
    sequence_timer = None

    # Functions for reading/updating the local sequences json
    # file.  Returns a dict, since the top-level type is object
    def getSequences():
        with open('sequences.json', 'r') as file:
            return load(file)

    def putSequences(data):
        with open('sequences.json', 'w') as file:
            return dump(data, file, sort_keys=False)

    # Returns string of currently active sequence id,
    # otherwise returns a blank string (not None)
    def getSequenceState():
        return '' if Sequencer.sequence == None else str(Sequencer.sequence)

    # Functional means for executing a sequence
    def executeSequence(index: int, sequence):
        if index > 0:
            Platelet.zoneOff(sequence[str(index - 1)]['zone'])
        if index < len(sequence) - 1:
            Platelet.zoneOn(sequence[str(index)]['zone'])
            Sequencer.sequence_timer = Timer(60.0 * sequence[str(index)]['minutes'],\
                    Sequencer.executeSequence, [index + 1, sequence])
            Sequencer.sequence_timer.start()
        else:
            Platelet.pumpOff()
            Sequencer.sequence = None
            Sequencer.sequence_timer = None

    # Sets up and activates the sequence with specified
    # id number
    def initSequence(id):
        if Sequencer.sequence == None:
            Sequencer.sequence = int(id)
            Sequencer.executeSequence(0, Sequencer.getSequences()[str(id)]['sequence'])

    # Cancels any currently active sequence (and heavy-handedly
    # turns off all zones for good measure)
    def cancelSequence():
        if Sequencer.sequence_timer != None:
            Sequencer.sequence_timer.cancel()
            Sequencer.sequence_timer = None
        for zone in app.config['ZONES']:
            relayOFF(zone[0], zone[1])
        Platelet.pumpOff()
        Sequencer.sequence = None

# Routes for the dashboard
#@app.route('/')
#def index():

# Routes for enabling and disabling single zones
#@app.route('/zone/')
@app.route('/')
def index():
    return redirect(url_for('zone'))

@app.route('/zone/')
def zone():
    state = Platelet.getState()
    actions=[ ( str(x), 'disable' if x in state else 'time',\
            {'zone': x}, x in state )\
            for x in range(1, app.config['NUM_ZONES'] + 1)]
    if app.config['PUMP_ZONE'] is not None:
        actions.append(('Pump',\
                'disable' if 'Pump' in state else 'time',\
                {'zone': 0}, 'Pump' in state ))
    return render_template('keypad.html',\
            confirm = False,\
            subject = 'zone',\
            prompt = 'Activate which zone?',\
            actions = actions\
            )

@app.route('/zone/time/<int:zone>/')
def time(zone):
    actions = [ (str(x), 'enable',\
              {'zone': zone, 'time': x}, False)\
              for x in app.config['TIMES'] ]
    actions.append(('Cancel', 'index', {}, False))
    prompt = ' '.join([
        'Activate zone',
        str(zone) if zone != 0 else 'pump',
        'for how many minutes?'
    ])
    return render_template('keypad.html',\
            confirm = True,\
            subject = 'time',\
            prompt = prompt,\
            actions = actions\
            )

# Web API for turning zones on and off
@app.route('/zone/disable/<int:zone>/')
def disable(zone):
    if zone == 0:
        Platelet.pumpOff()
        if Platelet.timers[0]:
            Platelet.timers[0].cancel()
            Platelet.timers[0] = None;
        flash('Pump was turned off.', 'success')
    else:
        Platelet.zoneOff(zone)
        if Platelet.timers[zone]:
            Platelet.timers[zone].cancel()
            Platelet.timers[zone] = None;
        flash(' '.join([
            'Zone', str(zone), 'was turned off.'
            ]), 'success')
    return redirect(url_for('index'))

@app.route('/zone/enable/<int:zone>/<int:time>/')
def enable(zone, time):
    if time <= app.config['MAX_TIME']:
        if zone == 0:
            Platelet.pumpOn()
            Platelet.timers[0] = Timer(60.0 * time, Platelet.pumpOff)
            Platelet.timers[0].start()
            flash(' '.join([
                'Pump was turned on for',
                str(time),
                'minute.' if time == 1 else 'minutes.'
                ]), 'success')
        else:
            Platelet.zoneOn(zone)
            Platelet.timers[zone] = Timer(60.0 * time, Platelet.zoneOff, [zone])
            Platelet.timers[zone].start()
            flash(' '.join([
                'Zone',
                str(zone),
                'was turned on for',
                str(time),
                'minute.' if time == 1 else 'minutes.'
                ]), 'success')
    return redirect(url_for('index'))

# Routes for the sequences page
@app.route('/sequence/')
def sequence():
    actions = { 'run': 'runSequence',
            'edit': 'editSequence',
            'delete': 'deleteSequence' }
    active = { 'stop': 'stopSequence' }
    fields = [ 'name', 'description', 'sequence' ]
    items = []
    for id, entry in Sequencer.getSequences().items():
        new_item = [id]
        new_item.append({ field: entry[field] for field in fields })
        if id == str(Sequencer.sequence):
            new_item.append([ (key.capitalize(), value, {}, True) for key, value in active.items() ])
            new_item.append(True)
        else:
            new_item.append([ (key.capitalize(), value, {'id': id}, True) for key, value in actions.items() ])
            new_item.append(False)
        items.append(new_item)
    return render_template('list.html', allow_create = True,\
            data_headings = ['zone', 'minutes'],\
            subject = 'sequence', items = items)

@app.route('/sequence/run/<int:id>/')
def runSequence(id):
    Sequencer.initSequence(id)
    flash(' '.join([
        'Started sequence',
        Sequencer.getSequences()[str(id)]['name'],
        '.'
        ]), 'success')
    return redirect(url_for('sequence'))

@app.route('/sequence/stop/')
def stopSequence():
    Sequencer.cancelSequence()
    flash('Sequence cancelled.', 'caution')
    return redirect(url_for('sequence'))

@app.route('/sequence/new/', methods=('GET', 'POST'))
def newSequence():
    id = str(max([int(x) for x in Sequencer.getSequences().keys()]) + 1)
    if request.method == 'POST':
        return redirect(url_for('editSequence', id = id), code = 307)
    return render_template('edit.html',\
            id = id,\
            subject = 'sequence',\
            item = {'name': '', 'description': '',\
            'sequence': {'0': {'zone': 1, 'minutes':1}, 'columns': ['zone','minutes']}},\
            fields = ['name', 'description', 'sequence'],\
            constrain = {'minutes': 120,\
                'zone':[ x for x in range(1, app.config['NUM_ZONES'] + 1)]},\
            num_zones=app.config['NUM_ZONES'])

@app.route('/sequence/edit/<int:id>/', methods=('GET', 'POST'))
def editSequence(id):
    if request.method == 'POST':
        sequences = Sequencer.getSequences()
        fields = ['description', 'name']
        resultant = {}
        resultant['created'] = strftime('%Y-%m-%dT%H:%M:%S.999Z') if str(id) not in sequences else sequences[str(id)]['created']
        for field in fields:
            if request.form[field] == '':
                resultant[field] = field
            else:
                resultant[field] = request.form[field]
        resultant['modified'] = strftime('%Y-%m-%dT%H:%M:%S.999Z')
        resultant['sequence'] = {\
            str(x): {'zone': y, 'minutes': z}\
            for x, (y,z)\
            in enumerate([\
                x for x\
                in zip([\
                    int(request.form.get(y)) for y in [\
                        z for z in list(request.form.keys())\
                        if match('zone-*', z)\
                    ]\
                ],[\
                    int(request.form.get(y)) for y in [\
                        z for z in list(request.form.keys())\
                        if match('minutes-*', z)\
                    ]\
                ])\
            ])\
        }
        resultant['sequence']['columns'] = ['zone', 'minutes']
        sequences.update({str(id): resultant})
        Sequencer.putSequences(sequences)
        flash(' '.join([
            'Sequence',
            resultant['name'],
            'updated.'
            ]), 'success')
        return redirect(url_for('sequence'))
    return render_template('edit.html',\
            id = str(id),\
            subject = 'sequence',\
            item = Sequencer.getSequences()[str(id)],\
            fields = ['name', 'description', 'sequence'],\
            constrain = {'minutes': app.config['MAX_TIME'],\
                'zone':[ x for x in range(1, app.config['NUM_ZONES'] + 1)]},\
            num_zones = app.config['NUM_ZONES'])

@app.route('/sequence/delete/<int:id>/')
def deleteSequence(id):
    sequences = Sequencer.getSequences()
    removed = sequences.pop(str(id))
    Sequencer.putSequences(sequences)
    flash(' '.join([
        'Sequence',
        removed['name'],
        'deleted.'
        ]), 'caution')
    return redirect(url_for('sequence'))

if __name__ == '__main__':
    import bjoern
    app.logger.info('Drizzle has started.')
    bjoern.run(app, '0.0.0.0', app.config['APP_PORT'])
