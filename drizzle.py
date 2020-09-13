from flask import Flask
from flask import render_template
app = Flask(__name__)

@app.route('/')
def index():
    state = 2
    active = [ x for x in range(0,7) if (state >> x) % 2 ]
    return render_template('index.html', active=active)

@app.route('/time/<int:id>/')
def time(id):
    return render_template('time.html', zone=id)

@app.route('/zone/<int:id>/<int:time>/')
def zone(id, time):
    return 'Turning on zone %d for %d minutes.' % (id, time)
