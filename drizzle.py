"""
A flask app for controlling relays, with a sprinkler flavour
"""
from json import load

from flask import Flask, redirect, request, url_for

app = Flask(__name__)
app.config.from_file("config.json", load=load)
app.logger.setLevel(app.config["LOG_LEVEL"])


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
    from blueprints.sequence import sequence
    from blueprints.zone import zone

app.register_blueprint(zone.zone)
app.register_blueprint(sequence.sequence)


@app.route("/")
def index():
    """
    Redirect to index view
    """
    return redirect(url_for("zone.zone_select"))


if __name__ == "__main__":
    import bjoern

    app.logger.info("Drizzle has started.")
    bjoern.run(app, "0.0.0.0", app.config["APP_PORT"])
