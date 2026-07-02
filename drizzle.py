"""
A flask app for controlling relays, with a sprinkler flavour
"""
from json import load, dump

from flask import Flask, flash, redirect, render_template, request, url_for
from wtforms import IntegerField, FieldList, FormField
from wtforms.validators import NumberRange, ValidationError
from util.filters import filter_capitalize_first, filter_pluralize

app = Flask(__name__)
config_path = "config/config.json"
app.config.from_file(config_path, load=load)
app.logger.setLevel(app.config["LOG_LEVEL"])
app.add_template_filter(filter_capitalize_first, 'capitalize')
app.add_template_filter(filter_pluralize, 'pluralize')


@app.before_request
def log_request():
    """
    Debug level output for every web request
    """
    app.logger.debug(
        " ".join(
            [
                str(x)
                for x in [
                    request.scheme,
                    request.remote_addr,
                    request.method,
                    request.path,
                ]
            ]
        )
    )


with app.app_context():
    from util.form import ConfigForm, RunningTimeForm
    from blueprints.dashboard import dashboard
    from blueprints.board import board
    from blueprints.relay import relay
    from blueprints.sequencer import sequencer
    from blueprints.schedule import schedule

app.register_blueprint(dashboard.dashboard)
app.register_blueprint(board.board)
app.register_blueprint(relay.relay)
app.register_blueprint(sequencer.sequencer)
app.register_blueprint(schedule.schedule)


@app.route("/")
def index():
    """
    Redirect to index view
    """
    return redirect(url_for("dashboard.index"))


@app.route("/config", methods=(["GET", "POST"]))
def edit_config():
    """
    Global configuration editor
    """
    def validate_running_time(form, field):
        if field.data > app.config["MAX_TIME"]:
            raise ValidationError(
                ' '.join(
                    [
                        "Running time",
                        str(field.data),
                        "is greater than the currently set",
                        "maximum allowable running time of",
                        str(app.config["MAX_TIME"]),
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
        form = EditConfigForm(data=app.config, meta={'csrf': False})
    else:
        form = EditConfigForm(meta={'csrf': False})
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate", "error")
            flash(form.errors, "error")
        else:
            app.config["RUNNING_TIMES"] = form["RUNNING_TIMES"].data
            for k in request.form.keys():
                if k.split('-')[0] != "RUNNING_TIMES":
                    app.config[k] = form[k].data
            with open(config_path, 'w', encoding="utf8") as f:
                dump(
                    {
                        k: app.config[k] for k in request.form.keys()
                        if k.split('-')[0] != "RUNNING_TIMES" and k != "submit"
                    } | {"RUNNING_TIMES": app.config["RUNNING_TIMES"]}, f
                )
            return redirect(url_for(".index"))
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
            "TESTING",
            "MAX_TIME",
            "MAX_CONCURRENT",
            "RUNNING_TIMES",
        ],
        allow_reorder=True,
        form=form,
    )


if __name__ == "__main__":
    import bjoern

    app.logger.info("Drizzle has started.")
    bjoern.run(app, "0.0.0.0", app.config["APP_PORT"])
