"""
Routes for scheduling relays and sequences
"""
from datetime import time
from operator import itemgetter
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
from wtforms import FieldList, FormField
from wtforms.validators import ValidationError

with current_app.app_context():
    from util.schedule import Schedule, Job, Scheduler
    from util.sequencer import Sequencer
    from util.form import FixtureForm, ScheduleForm
    from util.redirected import redirected
    from util.template import (
        filter_capitalize_first as capitalize,
        filter_pluralize as pluralize
    )
    schedules = Scheduler()
    sequences = Sequencer()
schedule = Blueprint("schedule", __name__, url_prefix="/schedule")

fields = ["name", "description", "jobs"]
redirected = redirected(
    schedules,
    current_app.config["SCHEDULE_NAME"],
    "index"
)

weekdays = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


@schedule.route("/")
def index():
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=[
            current_app.config["SEQUITUR_NAME"],
            "weekdays",
            "time",
        ],
        data_name=pluralize(current_app.config["JOB_NAME"]),
        subject=current_app.config["SCHEDULE_NAME"],
        items={
            id: {
                "fields": {
                    field: schedule.__getattribute__(field)
                    for field in fields
                    if field != "jobs"
                } | {
                    pluralize(current_app.config["JOB_NAME"]): {
                        ordinal: {
                            current_app.config["SEQUITUR_NAME"]: job.sequitur.name,
                            "weekdays": ", ".join(
                                weekdays[weekday] for weekday in job.weekdays
                            ),
                            "time": ':'.join([
                                str(job.time.hour),
                                str(job.time.minute),
                            ]) if job.time.minute > 9 else ":0".join([
                                str(job.time.hour),
                                str(job.time.minute),
                            ])
                        }
                        for ordinal, job in enumerate(schedule.jobs)
                    }
                },
                "actions": {
                    "inactive": {
                        "activate": {
                            "name": capitalize("activate"),
                            "endpoint": ".activate",
                            "args": {"schedule_id": id},
                        },
                        "edit": {
                            "name": capitalize("edit"),
                            "endpoint": ".edit",
                            "args": {"schedule_id": id},
                        },
                        "delete": {
                            "name": capitalize("delete"),
                            "endpoint": ".delete",
                            "args": {"schedule_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting",
                                current_app.config["SCHEDULE_NAME"],
                                schedule.name,
                                "cannot be undone."
                            ]),
                        }
                    },
                    "active": {
                        "deactivate": {
                            "name": capitalize("deactivate"),
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
    def validate_concurrency(form, field):
        if len(
            [
                str(weekday) + str(d.time.data.hour) +
                str(d.time.data.minute)
                for d in field.entries for weekday in d.weekdays.data
            ]
        ) > len(
            {
                str(weekday) + str(d.time.data.hour) +
                str(d.time.data.minute)
                for d in field.entries for weekday in d.weekdays.data
            }
        ):
            raise ValidationError(
                "Schedule must not contain concurrently scheduled jobs."
            )

    class EditScheduleForm(ScheduleForm):
        jobs = FieldList(
            FormField(FixtureForm),
            validators=[validate_concurrency]
        )

    schedule = schedules[schedule_id] if schedule_id in schedules.keys(
    ) else Schedule(
        **{
            "id": schedule_id,
            "name": ' '.join(
                [
                    capitalize(current_app.config["SCHEDULE_NAME"]),
                    ''.join(choices(ascii_uppercase, k=5)),
                ]
            ),
            "description": "A " + current_app.config["SCHEDULE_NAME"],
            "active": False,
            "jobs": [Job(str(next(iter(sequences.values()))), 0, time())]
        }
    )
    if request.method == "GET":
        form = EditScheduleForm(
            formdata=None, obj=schedule, meta={'csrf': False}
        )
    else:
        form = EditScheduleForm(meta={'csrf': False})
    for job in form.jobs.entries:
        job.sequitur.choices = sorted(
            list(
                (s.id, s.name)
                for s in sequences.values()
            ),
            key=itemgetter(1)
        )
        job.weekdays.choices = list(
            (id, weekday) for id, weekday in enumerate(weekdays)
        )
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate: " + str(form.errors), "error")
        else:
            while len(form.jobs.entries) > len(schedule.jobs):
                schedule.jobs += [Job(None, 0, time())]
            form.populate_obj(schedule)
            for job in schedule.jobs:
                job.sequitur = sequences[job.sequitur]
            schedules[schedule_id] = schedule
            flash(
                ' '.join(
                    [
                        "Updated",
                        current_app.config["SCHEDULE_NAME"],
                        schedule.name + '.',
                    ]
                ), "success"
            )
            return redirect(url_for(".index"))
    return render_template(
        "edit.html",
        title="edit " + current_app.config["SCHEDULE_NAME"],
        describe=" ".join(
            [
                "Change the settings, and",
                "change, move, add, delete entries for",
                current_app.config["SCHEDULE_NAME"],
                schedule.name,
                "in the fields below."
            ]
        ),
        data_name=current_app.config["JOB_NAME"],
        subject=current_app.config["SCHEDULE_NAME"],
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
