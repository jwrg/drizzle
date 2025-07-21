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
            relay.name,
            "deactivate" if id in state.keys() else "activate",
            "relay.disable" if id in state.keys() else "relay.enable",
            {"relay_id": id},
            True,
            id in state.keys(),
            state[id] if id in state.keys() else None,
        )
        for id, relay in Platelet.relays.items()
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


@relay.route("/disable/<string:relay_id>/", methods=(["POST"]))
def disable(relay_id):
    """
    API command for turning off a relay, given its id
    """
    Platelet.relay_off(relay_id)
    flash(
        " ".join(
            [
                "Relay", Platelet.relays[relay_id].name,
                "was turned off."
            ]
        ),
        "success"
    )
    return redirect(url_for("index"))


@relay.route("/enable/<string:relay_id>/", methods=(["POST"]))
def enable(relay_id):
    """
    API command that activates a relay specified by id for a given number of minutes
    """
    interval = int(request.form["time"])
    if interval <= Platelet.max_minutes:
        if len(Platelet.get_state()) == Platelet.max_relays:
            flash(
                " ".join(
                    [
                        "Relay",
                        Platelet.relays[relay_id].name,
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
                        Platelet.relays[relay_id].name,
                        "was turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                    ]
                ),
                "success",
            )
    return redirect(url_for("index"))
