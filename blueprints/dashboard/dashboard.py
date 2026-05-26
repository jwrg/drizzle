"""
Routes for configuring the app
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
    from util.board import Holder
    from util.relay import Baton
    from util.sequencer import Sequencer
    from util.schedule import Scheduler
    from util.template import (
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
        "keypad.html",
        subject="dashboard",
        actions=[
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
        ],
        datetime=datetime.now().strftime("%d/%m/%y %H:%M:%S"),
        times=(
            x["time"] for x in current_app.config["RUNNING_TIMES"]
            if x["time"] <= current_app.config["MAX_TIME"]
        ),
    )
