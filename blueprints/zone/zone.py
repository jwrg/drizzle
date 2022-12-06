"""
Routes for activating relay timers
"""
from flask import Blueprint, current_app, flash, redirect, render_template, url_for

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
            "zone.disable" if x in state else "zone.time_select",
            {"zone_id": x},
            x in state,
        )
        for x in range(1, current_app.config["NUM_ZONES"] + 1)
    ]
    if current_app.config["PUMP_ZONE"] is not None:
        actions.append(
            (
                "Pump",
                "zone.disable" if "Pump" in state else "zone.time_select",
                {"zone_id": 0},
                "Pump" in state,
            )
        )
    return render_template(
        "keypad.html",
        confirm=False,
        subject="zone",
        prompt="Activate which zone?",
        actions=actions,
    )


@zone.route("/time/<int:zone_id>/")
def time_select(zone_id):
    """
    View that selects the activation time interval, given the id number
    """
    actions = [
        (str(x), "zone.enable", {"zone_id": zone_id, "interval": x}, False)
        for x in current_app.config["TIMES"]
    ]
    actions.append(("Cancel", "index", {}, False))
    prompt = " ".join(
        [
            "Activate zone",
            str(zone_id) if zone_id != 0 else "pump",
            "for how many minutes?",
        ]
    )
    return render_template(
        "keypad.html",
        confirm=True,
        subject="time",
        prompt=prompt,
        actions=actions,
    )


@zone.route("/zone/disable/<int:zone_id>/")
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


@zone.route("/zone/enable/<int:zone_id>/<int:interval>/")
def enable(zone_id, interval):
    """
    API command that activates a zone specified by id number for a given number of minutes
    """
    if interval <= current_app.config["MAX_TIME"]:
        if zone_id == 0:
            Platelet.pump_on(interval)
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
            Platelet.zone_on(zone_id, interval)
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
