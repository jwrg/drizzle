"""
Routes for activating relay timers
"""
from datetime import timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

with current_app.app_context():
    from util.platelet import Platelet

zone = Blueprint("zone", __name__, url_prefix="/zone")


@zone.route("/")
def zone_select():
    """
    View that selects the zone to activate
    """
    state = Platelet.get_state()
    actions = [
        (
            str(x),
            "deactivate" if x in state.keys() else "activate",
            "zone.disable" if x in state.keys() else "zone.enable",
            {"zone_id": x},
            True,
            x in state.keys(),
            state[x] if x in state.keys() else None,
        )
        for x in range(1, Platelet.num_zones + 1)
    ]
    if Platelet.pump_zone is not None:
        actions.append(
            (
                "Pump",
                "deactivate" if "Pump" in state.keys() else "activate",
                "zone.disable" if "Pump" in state.keys() else "zone.enable",
                {"zone_id": 0},
                True,
                "Pump" in state.keys(),
                state["Pump"] if "Pump" in state.keys() else None,
            )
        )
    return render_template(
        "keypad.html",
        subject="zone",
        prompt="Activate which zone?",
        actions=actions,
        min_minutes=Platelet.min_minutes,
        max_minutes=Platelet.max_minutes,
    )


@zone.route("/zone/disable/<int:zone_id>/", methods=(["POST"]))
def disable(zone_id):
    """
    API command for turning off a zone, given its id number
    """
    if zone_id == 0:
        Platelet.pump_off()
        flash("Pump was turned off.", "success")
    else:
        Platelet.zone_off(zone_id)
        flash(" ".join(["Zone", str(zone_id), "was turned off."]), "success")
    return redirect(url_for("index"))


@zone.route("/zone/enable/<int:zone_id>/", methods=(["POST"]))
def enable(zone_id):
    """
    API command that activates a zone specified by id number for a given number of minutes
    """
    interval = int(request.form["time"])
    if interval <= Platelet.max_minutes:
        if zone_id == 0:
            Platelet.pump_on(timedelta(minutes=interval))
            flash(
                " ".join(
                    [
                        "Pump was turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                    ]
                ),
                "success",
            )
        else:
            Platelet.zone_on(zone_id, timedelta(minutes=interval))
            flash(
                " ".join(
                    [
                        "Zone",
                        str(zone_id),
                        "was turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                    ]
                ),
                "success",
            )
    return redirect(url_for("index"))
