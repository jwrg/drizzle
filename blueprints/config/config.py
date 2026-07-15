"""
Routes for configuring the application itself
"""
from json import dump
from os import path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from wtforms import IntegerField, FieldList, FormField
from wtforms.validators import NumberRange, ValidationError

from util.filters import (
    filter_capitalize_first as capitalize,
    filter_pluralize as pluralize
)

with current_app.app_context():
    from util.form import ConfigForm, RunningTimeForm

config = Blueprint("config", __name__, url_prefix="/config")

config_path = "config/"


@config.route("/", methods=(["GET", "POST"]))
def index():
    """
    Global configuration editor
    """
    def validate_running_time(form, field):
        if field.data > current_app.config["MAX_TIME"]:
            raise ValidationError(
                ' '.join(
                    [
                        "Running time",
                        str(field.data),
                        "is greater than the currently set",
                        "maximum allowable running time of",
                        str(current_app.config["MAX_TIME"]),
                        "minutes" + '.',
                    ]
                )
            )

    class EditRunningTimeForm(RunningTimeForm):
        time = IntegerField("Running time", validators=[
            NumberRange(min=1),
            validate_running_time,
        ])

    class EditConfigForm(ConfigForm):
        RUNNING_TIMES = FieldList(FormField(EditRunningTimeForm))

    if request.method == "GET":
        form = EditConfigForm(data=current_app.config, meta={'csrf': False})
    else:
        form = EditConfigForm(meta={'csrf': False})
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate", "error")
            flash(form.errors, "error")
        else:
            current_app.config["RUNNING_TIMES"] = form["RUNNING_TIMES"].data
            for k in request.form.keys():
                if k.split('-')[0] != "RUNNING_TIMES":
                    current_app.config[k] = form[k].data
            with open(
                path.join(
                    config_path,
                    "config.json"
                ),
                'w',
                encoding="utf8"
            ) as f:
                dump(
                    {
                        k: current_app.config[k] for k in request.form.keys()
                        if k.split('-')[0] != "RUNNING_TIMES" and k != "submit"
                    } | {"RUNNING_TIMES": current_app.config["RUNNING_TIMES"]},
                    f
                )
            return redirect(url_for("index"))
    return render_template(
        "edit.html",
        title="edit global app configuration",
        describe='. '.join([
            "Change global app settings here",
            "If unsure, leave these alone",
        ]),
        subject="config",
        data_name="running time",
        fields=[
            "BOARD_NAME",
            "CONNECTION_NAME",
            "RELAY_NAME",
            "DEPENDENCY_NAME",
            "SEQUITUR_NAME",
            "SEQUENCIA_NAME",
            "SCHEDULE_NAME",
            "JOB_NAME",
            "LOG_LEVEL",
            "APP_PORT",
            "SECRET_KEY",
            "SERVER_NAME",
            "MAX_TIME",
            "MAX_CONCURRENT",
            "TIME_SELECTOR",
            "RUNNING_TIMES",
        ],
        allow_reorder=True,
        form=form,
    )
