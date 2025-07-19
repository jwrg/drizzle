"""
Routes for activating relay timers
"""
from datetime import timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

with current_app.app_context():
    from util.platelet import Platelet

relay = Blueprint("relay", __name__, url_prefix="/relay")


@relay.route("/")
def relay_select():
    """
    View that selects the relay to activate
    """
    state = Platelet.get_state()
    actions = [
        (
            v.name,
            "deactivate" if v.name in state.keys() else "activate",
            "relay.disable" if v.name in state.keys() else "relay.enable",
            {"relay_id": v.name},
            True,
            v.name in state.keys(),
            state[v.name] if v.name in state.keys() else None,
        )
        for k, v in Platelet.relays.items()
    ]
    return render_template(
        "keypad.html",
        subject="relay",
        prompt="Activate which relay?",
        actions=actions,
        min_minutes=Platelet.min_minutes,
        max_minutes=Platelet.max_minutes,
        default_minutes=Platelet.default_minutes,
    )


@relay.route("/relay/disable/<string:relay_id>/", methods=(["POST"]))
def disable(relay_id):
    """
    API command for turning off a relay, given its id number
    """
    Platelet.relay_off(relay_id)
    flash(" ".join(["Relay", str(relay_id), "was turned off."]), "success")
    return redirect(url_for("index"))


@relay.route("/relay/enable/<string:relay_id>/", methods=(["POST"]))
def enable(relay_id):
    """
    API command that activates a relay specified by id number for a given number of minutes
    """
    interval = int(request.form["time"])
    if interval <= Platelet.max_minutes:
        if len(Platelet.get_state()) == Platelet.max_relays:
            flash(
                " ".join(
                    [
                        "Relay",
                        relay_id,
                        "was not turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                        "Maximum number of active relays (",
                        str(Platelet.max_relays),
                        ") reached."
                    ]
                ),
                "error",
            )
        else:
            Platelet.relay_on(relay_id, timedelta(minutes=interval))
            flash(
                " ".join(
                    [
                        "Relay",
                        relay_id,
                        "was turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                    ]
                ),
                "success",
            )
    return redirect(url_for("index"))
