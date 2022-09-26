from flask import Blueprint, current_app, flash, render_template, redirect, url_for

with current_app.app_context(): 
    from util.Platelet import Platelet

zone = Blueprint('zone', __name__, url_prefix='/zone')

@zone.route('/')
def zoneSelect():
    state = Platelet.getState()
    actions=[ ( str(x), 'zone.disable' if x in state else 'zone.timeSelect',\
            {'zone': x}, x in state )\
            for x in range(1, current_app.config['NUM_ZONES'] + 1)]
    if current_app.config['PUMP_ZONE'] is not None:
        actions.append(('Pump',\
                'zone.disable' if 'Pump' in state else 'zone.timeSelect',\
                {'zone': 0}, 'Pump' in state ))
    return render_template('keypad.html',\
            confirm = False,\
            subject = 'zone',\
            prompt = 'Activate which zone?',\
            actions = actions\
            )

@zone.route('/time/<int:zone>/')
def timeSelect(zone):
    actions = [ (str(x), 'zone.enable',\
              {'zone': zone, 'time': x}, False)\
              for x in current_app.config['TIMES'] ]
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
@zone.route('/zone/disable/<int:zone>/')
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

@zone.route('/zone/enable/<int:zone>/<int:time>/')
def enable(zone, time):
    if time <= current_app.config['MAX_TIME']:
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
