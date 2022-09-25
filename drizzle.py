from json import dump, load
from re import match
from time import strftime
from flask import Flask, flash, render_template, redirect, request, url_for
app = Flask(__name__)
app.config.from_file('config.json', load=load)
app.logger.setLevel(app.config['LOG_LEVEL'])
with app.app_context(): 
    from util.Platelet import Platelet
    from util.Sequencer import Sequencer

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

# NB that the interface starts counting zones at one
# but zone tuples are zero-indexed.  Relays on the
# boards start at K1 and so the first relay is relay
# 1, since there is no K0.  Not confusing at all.

# Don't forget the zone number for the pump switch (to
# denote that no pump is used, give the value as None)

# Request debug logging
@app.before_request
def log_request():
    app.logger.debug(' '.join([ str(x) for x in [
        request.remote_addr,
        request.method,
        request.path,
        request.scheme
        ]]))

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
        flash('Pump was turned off.', 'success')
    else:
        Platelet.zoneOff(zone)
        flash(' '.join([
            'Zone', str(zone), 'was turned off.'
            ]), 'success')
    return redirect(url_for('index'))

@app.route('/zone/enable/<int:zone>/<int:time>/')
def enable(zone, time):
    if time <= app.config['MAX_TIME']:
        if zone == 0:
            Platelet.pumpOn(time)
            flash(' '.join([
                'Pump was turned on for',
                str(time),
                'minute.' if time == 1 else 'minutes.'
                ]), 'success')
        else:
            Platelet.zoneOn(zone, time)
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
