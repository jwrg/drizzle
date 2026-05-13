"""
A flask app for controlling relays, with a sprinkler flavour
"""
from json import load, dump

from flask import Flask, flash, redirect, render_template, request, url_for
from util.template import filter_capitalize_first, filter_pluralize

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
    from util.form import ConfigForm
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
    if request.method == "GET":
        form = ConfigForm(data=app.config, meta={'csrf': False})
    else:
        form = ConfigForm(meta={'csrf': False})
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate", "error")
            flash(form.errors, "error")
        else:
            for k in request.form.keys():
                app.config[k] = form[k].data
            with open(config_path, 'w', encoding="utf8") as f:
                dump(
                    {
                        k: app.config[k] for k in request.form.keys()
                        if k != "submit"
                    }, f
                )
            return redirect(url_for(".index"))
    return render_template(
        "edit.html",
        title="edit global app configuration",
        describe="Change global app settings here. If unsure, leave this alone.",
        subject="config",
        fields=[
            "MAX_TIME",
            "MAX_CONCURRENT",
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
        ],
        form=form,
    )


if __name__ == "__main__":
    import bjoern

    app.logger.info("Drizzle has started.")
    bjoern.run(app, "0.0.0.0", app.config["APP_PORT"])
