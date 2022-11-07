from json import load
from flask import Flask, redirect, request, url_for

app = Flask(__name__)
app.config.from_file("config.json", load=load)
app.logger.setLevel(app.config["LOG_LEVEL"])


@app.before_request
def log_request():
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
    from blueprints.zone import zone
    from blueprints.sequence import sequence

app.register_blueprint(zone.zone)
app.register_blueprint(sequence.sequence)


@app.route("/")
def index():
    return redirect(url_for("zone.zoneSelect"))


if __name__ == "__main__":
    import bjoern

    app.logger.info("Drizzle has started.")
    bjoern.run(app, "0.0.0.0", app.config["APP_PORT"])
