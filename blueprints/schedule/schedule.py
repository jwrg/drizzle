"""
Routes for scheduling relays and sequences
"""
from random import choices
from string import ascii_uppercase, ascii_lowercase, digits

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
    from util.schedule import Schedule, Job, Scheduler
    from util.sequencer import Sequencer
    from util.form import ScheduleForm
    from util.redirected import redirected
    schedules = Scheduler()
    sequences = Sequencer()
schedule = Blueprint("schedule", __name__, url_prefix="/schedule")

fields = ["name", "description", "jobs"]
redirected = redirected(schedules, "schedule", ".index")

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
def index():
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
        items={
            id: {
                "fields": {
                    field: schedule.__getattribute__(field)
                    for field in fields
                    if field != "jobs"
                } | {
                    "jobs": {
                        ordinal: {
                            "sequence": job.sequence.name,
                            "weekday": weekdays[job.weekday],
                            "time": str(job.hour) + ":" + str(job.minute)
                        }
                        for ordinal, job in enumerate(schedule.jobs)
                    }
                },
                "actions": {
                    "inactive": {
                        "activate": {
                            "name": "activate".capitalize(),
                            "endpoint": ".activate",
                            "args": {"schedule_id": id},
                        },
                        "edit": {
                            "name": "edit".capitalize(),
                            "endpoint": ".edit",
                            "args": {"schedule_id": id},
                        },
                        "delete": {
                            "name": "delete".capitalize(),
                            "endpoint": ".delete",
                            "args": {"schedule_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting schedule",
                                schedule.name,
                                "cannot be undone."
                            ]),
                        }
                    },
                    "active": {
                        "deactivate": {
                            "name": "deactivate".capitalize(),
                            "endpoint": ".deactivate",
                            "args": {"schedule_id": id},
                        },
                    },
                    "always": {
                    },
                },
                "active": schedule.active
            }
            for id, schedule in schedules.items()
        }
    )


@schedule.route("/new/", methods=("GET", "POST"))
def new():
    return redirect(
        url_for(
            ".edit", schedule_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@schedule.route("/edit/<string:schedule_id>/", methods=("GET", "POST"))
def edit(schedule_id):
    schedule = schedules[schedule_id] if schedule_id in schedules.keys(
    ) else Schedule(
        **{
            "id": schedule_id,
            "name": "New Schedule" + ''.join(choices(ascii_uppercase, k=5)),
            "description": "A new schedule of sequences",
            "active": False,
            "jobs": [Job(str(next(iter(sequences.values()))), 0, 0, 0)]
        }
    )
    if request.method == "GET":
        form = ScheduleForm(formdata=None, obj=schedule, meta={'csrf': False})
    else:
        form = ScheduleForm(meta={'csrf': False})
    for entry in form.jobs.entries:
        entry.weekday.choices = [
            (id, weekday) for id, weekday in weekdays.items()
        ]
        entry.sequence.choices = [
            (sequitur.id, sequitur.name)
            for sequitur in sequences.values()
        ]
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate", "error")
            flash(form.errors, "error")
        else:
            while len(form.jobs.entries) > len(schedule.jobs):
                schedule.jobs += [Job(None, 0, 0, 0)]
            form.populate_obj(schedule)
            for job in schedule.jobs:
                job.sequence = sequences[job.sequence]
            schedules[schedule_id] = schedule
            flash("Updated schedule " + schedule.name, "success")
            return redirect(url_for(".index"))
    return render_template(
        "edit.html",
        id=str(schedule_id),
        title="edit schedule configuration",
        describe=" ".join(
            [
                "change the settings for schedule",
                schedule.name,
                "in the fields below."
            ]
        ),
        subject="schedule",
        fields=fields,
        form=form,
    )


@schedule.route("/delete/<string:schedule_id>/")
@redirected()
def delete(schedule_id):
    del schedules[schedule_id]


@schedule.route("/activate/<string:schedule_id>/")
@redirected()
def activate(schedule_id):
    schedules[schedule_id].on()
    schedules.save()


@schedule.route("/deactivate/<string:schedule_id>/")
@redirected()
def deactivate(schedule_id):
    schedules[schedule_id].off()
    schedules.save()
