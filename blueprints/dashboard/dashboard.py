"""
Routes for quick and dirty interactions with the app
"""
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

with current_app.app_context():
    from lib.board import Holder
    from lib.relay import Baton
    from lib.sequencer import Sequencer
    from lib.schedule import Scheduler
    from util.filters import (
        filter_capitalize_first as capitalize,
        filter_pluralize as pluralize
    )
    boards = Holder()
    relays = Baton()
    sequences = Sequencer()
    schedules = Scheduler()

dashboard = Blueprint("dashboard", __name__, url_prefix="/dashboard")

fields = ["name", "description", "type", "index", "active"]


@dashboard.route("/")
def index():
    """
    View that selects the relay to activate
    """
    state = relays.state()
    return render_template(
        "dashboard.html",
        subject="dashboard",
        datetime=datetime.now().strftime("%d/%m/%y %H:%M:%S"),
        relays=(
            (
                relay.name,
                "turn off" if id in state.keys() else "turn on",
                "relay.off" if id in state.keys() else "relay.on",
                {"relay_id": id},
                True,
                id in state.keys(),
                relay.visible,
                state[id] if id in state.keys() else None,
            )
            for id, relay in relays.items()
        ),
        times=(
            x["time"] for x in current_app.config["RUNNING_TIMES"]
            if x["time"] <= current_app.config["MAX_TIME"]
        ),
        sequences=(
            (
                sequitur.name,
                "stop" if sequitur.running else "start",
                "sequencer.stop" if sequitur.running else "sequencer.start",
                {"sequence_id": sequitur.id},
                True,
                sequitur.running,
                sequitur.current.name if sequitur.running else "not running",
                sequitur.current.timer.remaining().total_seconds() if sequitur.running else "n/a",
            )
            for sequitur in sequences.values()
        ),
        schedules=(
            (
                schedule.name,
                "deactivate" if schedule.active else "activate",
                "schedule.deactivate" if schedule.active else "schedule.activate",
                {"schedule_id": schedule.id},
                True,
                schedule.active,
                schedule.jobs[0].sequitur.name if schedule.active else "not active",
                schedule.jobs[0].upcoming() if schedule.active else "n/a",
            )
            for schedule in schedules.values()
        ),
    )
