"""
Routes for scheduling relays and sequences
"""
from re import match
from time import strftime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

with current_app.app_context():
    from util.jsonny import Jsonny
    from util.schedule import Scheduler
schedule = Blueprint("schedule", __name__, url_prefix="/schedule")

scheduler = Scheduler()
weekdays = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}


@schedule.route("/")
def list_schedules():
    """
    View that lists all stored schedules
    """
    actions = {
        "activate": "schedule.activate_schedule",
        "edit": "schedule.edit_schedule",
        "delete": "schedule.delete_schedule",
    }

    active = {
        "deactivate": "schedule.deactivate_schedule",
        "edit": "schedule.edit_schedule",
        "delete": "schedule.delete_schedule",
    }
    fields = ["name", "description", "jobs"]
    items = []
    for schedule_id, entry in Jsonny.get("schedules").items():
        for _, job in entry["jobs"].items():
            job["time"] = ":".join(
                [
                    str(job["hour"]) if job["hour"] > 9 else "0" + str(job["hour"]),
                    str(job["minute"])
                    if job["minute"] > 9
                    else "0" + str(job["minute"]),
                ]
            )
            del job["hour"]
            del job["minute"]
            job["weekday"] = weekdays[job["weekday"]]
            job["sequence"] = Jsonny.get("sequences")[str(job["sequence"])]["name"]
            new_item = [schedule_id]
        new_item.append({field: entry[field] for field in fields})
        if entry["active"]:
            new_item.append(
                [
                    (
                        key.capitalize(),
                        value,
                        {"schedule_id": schedule_id},
                        key == "delete",
                    )
                    for key, value in active.items()
                ]
            )
            new_item.append(True)
        else:
            new_item.append(
                [
                    (
                        key.capitalize(),
                        value,
                        {"schedule_id": schedule_id},
                        key == "delete",
                    )
                    for key, value in actions.items()
                ]
            )
            new_item.append(False)
        items.append(new_item)
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=[
            "sequence",
            "weekday",
            "time",
        ],
        data_name="jobs",
        subject="schedule",
        items=items,
    )


@schedule.route("/activate/<int:schedule_id>/")
def activate_schedule(schedule_id):
    """
    API command that sets a schedule as active
    """
    scheduler.activate(schedule_id)
    return redirect(url_for(".list_schedules"))


@schedule.route("/deactivate/<int:schedule_id>/")
def deactivate_schedule(schedule_id):
    """
    API command that sets a schedule as inactive
    """
    scheduler.deactivate(schedule_id)
    return redirect(url_for(".list_schedules"))


@schedule.route("/new/", methods=("GET", "POST"))
def new_schedule():
    """
    View that creates a new schedule
    """
    schedule_id = str(max(int(x) for x in Jsonny.get("schedules").keys()) + 1)
    if request.method == "POST":
        return redirect(url_for(".edit_schedule", schedule_id=schedule_id), code=307)
    return render_template(
        "edit.html",
        id=schedule_id,
        subject="schedule",
        item={
            "name": "",
            "description": "",
            "jobs": {
                "0": {
                    "sequence": 0,
                    "weekday": 0,
                    "hour": 0,
                    "minute": 0,
                    "time": "00:00",
                },
            },
        },
        fields=["name", "description", "jobs"],
        data_headings=["sequence", "weekday", "time"],
        constrain={
            "sequence": {
                int(key): entry["name"]
                for key, entry in Jsonny.get("sequences").items()
            },
            "weekday": weekdays,
            "time": "time",
        },
    )


@schedule.route("/edit/<int:schedule_id>/", methods=("GET", "POST"))
def edit_schedule(schedule_id):
    """
    View that edits a schedule, given its id number
    """
    schedules = Jsonny.get("schedules")
    if request.method == "POST":
        fields = ["description", "name"]
        resultant = {}

        resultant["active"] = (
            False
            if str(schedule_id) not in schedules.keys()
            else schedules[str(schedule_id)]["active"]
        )
        resultant["created"] = (
            strftime("%Y-%m-%dT%H:%M:%S.999Z")
            if str(schedule_id) not in schedules
            else schedules[str(schedule_id)]["created"]
        )
        for field in fields:
            if request.form[field] == "":
                resultant[field] = field
            else:
                resultant[field] = request.form[field]
        resultant["modified"] = strftime("%Y-%m-%dT%H:%M:%S.999Z")
        resultant["jobs"] = {
            str(p): {"sequence": q, "weekday": r, "hour": s, "minute": t}
            for p, (q, r, s, t) in enumerate(
                list(
                    zip(
                        [
                            int(request.form.get(y))
                            for y in [
                                z for z in request.form.keys() if match("sequence-*", z)
                            ]
                        ],
                        [
                            int(request.form.get(y))
                            for y in [
                                z for z in request.form.keys() if match("weekday-*", z)
                            ]
                        ],
                        [
                            int(request.form.get(y)[0:2])
                            for y in [
                                z for z in request.form.keys() if match("time-*", z)
                            ]
                        ],
                        [
                            int(request.form.get(y)[3:5])
                            for y in [
                                z for z in request.form.keys() if match("time-*", z)
                            ]
                        ],
                    )
                )
            )
        }
        if len(
            [
                dict(y)
                for y in set(
                    tuple(x.items())
                    for x in list(
                        map(
                            lambda x: {key: x[key] for key in x if key != "sequence"},
                            resultant["jobs"].values(),
                        )
                    )
                )
            ]
        ) < len(list(resultant["jobs"].values())):
            flash(
                "Jobs may not be scheduled concurrently.  Please remove concurrently scheduled jobs",
                "error",
            )
            for key, job in resultant["jobs"].items():
                job["time"] = ":".join(
                    [
                        str(job["hour"]) if job["hour"] > 9 else "0" + str(job["hour"]),
                        str(job["minute"])
                        if job["minute"] > 9
                        else "0" + str(job["minute"]),
                    ]
                )
            return render_template(
                "edit.html",
                id=str(schedule_id),
                subject="schedule",
                item=resultant,
                fields=["name", "description", "jobs"],
                data_headings=["sequence", "weekday", "time"],
                constrain={
                    "sequence": {
                        int(key): entry["name"]
                        for key, entry in Jsonny.get("sequences").items()
                    },
                    "weekday": weekdays,
                    "time": "time",
                },
            )
        schedules.update({str(schedule_id): resultant})
        Jsonny.put("schedules", schedules)
        scheduler.reload()
        return redirect(url_for(".list_schedules"))
    for key, job in schedules[str(schedule_id)]["jobs"].items():
        job["time"] = ":".join(
            [
                str(job["hour"]) if job["hour"] > 9 else "0" + str(job["hour"]),
                str(job["minute"]) if job["minute"] > 9 else "0" + str(job["minute"]),
            ]
        )
    return render_template(
        "edit.html",
        id=str(schedule_id),
        subject="schedule",
        item=schedules[str(schedule_id)],
        fields=["name", "description", "jobs"],
        data_headings=["sequence", "weekday", "time"],
        constrain={
            "sequence": {
                int(key): entry["name"]
                for key, entry in Jsonny.get("sequences").items()
            },
            "weekday": weekdays,
            "time": "time",
        },
    )


@schedule.route("/delete/<int:schedule_id>/")
def delete_schedule(schedule_id):
    """
    API command that deletes a schedule given its id number
    """
    schedules = Jsonny.get("schedules")
    removed = schedules.pop(str(schedule_id))
    Jsonny.put("schedules", schedules)
    flash(" ".join(["Schedule", removed["name"], "deleted."]), "caution")
    return redirect(url_for(".list_schedules"))
