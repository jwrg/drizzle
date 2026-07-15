"""
A flask app for controlling relays, with a sprinkler flavour
"""
from json import load

from flask import Flask, redirect, request, url_for

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
    from blueprints.config import config
    from blueprints.dashboard import dashboard
    from blueprints.board import board
    from blueprints.relay import relay
    from blueprints.sequencer import sequencer
    from blueprints.schedule import schedule

app.register_blueprint(config.config)
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


if __name__ == "__main__":
    import bjoern

    app.logger.info("Drizzle has started.")
    bjoern.run(app, "0.0.0.0", app.config["APP_PORT"])
