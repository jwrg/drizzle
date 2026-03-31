"""
A flask app for controlling relays, with a sprinkler flavour
"""
from json import load

from flask import Flask, redirect, request, url_for
from util.template import filter_capitalize_all, filter_pluralize

app = Flask(__name__)
app.config.from_file("config/config.json", load=load)
app.logger.setLevel(app.config["LOG_LEVEL"])
app.add_template_filter(filter_capitalize_all, 'capitalize')
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
                    request.remote_addr,
                    request.method,
                    request.path,
                    request.scheme,
                ]
            ]
        )
    )


with app.app_context():
    from blueprints.board import board
    from blueprints.relay import relay
    from blueprints.sequence import sequence
    from blueprints.schedule import schedule

app.register_blueprint(board.board)
app.register_blueprint(relay.relay)
app.register_blueprint(sequence.sequence)
app.register_blueprint(schedule.schedule)


@app.route("/")
def index():
    """
    Redirect to index view
    """
    return redirect(url_for("relay.select_relay"))


if __name__ == "__main__":
    import bjoern

    app.logger.info("Drizzle has started.")
    bjoern.run(app, "0.0.0.0", app.config["APP_PORT"])
