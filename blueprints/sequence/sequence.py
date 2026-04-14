"""
Routes for sequencing relays
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
    from util.sequencer import Sequor, Sequitur, Sequencer
    from util.form import SequiturForm
    from util.relay import Baton
    from util.redirected import redirected
    relays = Baton()
    sequences = Sequencer()
sequence = Blueprint("sequence", __name__, url_prefix="/sequence")

fields = ["name", "description", "sequence"]
redirected = redirected(
    sequences,
    current_app.config["SEQUITUR_NAME"],
    ".index"
)


@sequence.route("/")
def index():
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=["index", current_app.config["RELAY_NAME"], "minutes"],
        data_name="sequence",
        subject=current_app.config["SEQUITUR_NAME"],
        items={
            id: {
                "fields": {
                    field: seq.__getattribute__(field)
                    for field in fields
                    if field != "sequence"
                } | {
                    "sequence": {
                        ordinal: {
                            "index": int(ordinal) + 1,
                            current_app.config["RELAY_NAME"]: entry.relay.name,
                            "minutes": str(entry.minutes)
                        }
                        for ordinal, entry in enumerate(seq.sequence)
                    }
                },
                "actions": {
                    "stopped": {
                        "start": {
                            "name": "start".capitalize(),
                            "endpoint": ".start",
                            "args": {"sequence_id": id},
                        },
                        "edit": {
                            "name": "edit".capitalize(),
                            "endpoint": ".edit",
                            "args": {"sequence_id": id},
                        },
                        "delete": {
                            "name": "delete".capitalize(),
                            "endpoint": ".delete",
                            "args": {"sequence_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting",
                                seq.name,
                                "cannot be undone.",
                            ]),
                        }
                    },
                    "running": {
                        "stop": {
                            "name": "stop".capitalize(),
                            "endpoint": ".stop",
                            "args": {"sequence_id": id},
                        },
                    },
                    "always": {
                    },
                },
                "running": seq.running,
                "active": True
            }
            for id, seq in sequences.items()
        }
    )


@sequence.route("/new/", methods=("GET", "POST"))
def new():
    return redirect(
        url_for(
            ".edit", sequence_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@sequence.route("/edit/<string:sequence_id>/", methods=("GET", "POST"))
def edit(sequence_id):
    seq = sequences[sequence_id] if sequence_id in sequences.keys(
    ) else Sequitur(
        **{
            "id": sequence_id,
            "name": ' '.join(
                [
                    current_app.config["SEQUITUR_NAME"].capitalize(),
                    ''.join(choices(ascii_uppercase, k=5)),
                ]
            ),
            "description": "A " + current_app.config["SEQUITUR_NAME"],
            "sequence": [Sequor(str(next(iter(relays.values()))), 1)]
        }
    )
    if request.method == "GET":
        form = SequiturForm(formdata=None, obj=seq, meta={'csrf': False})
    else:
        form = SequiturForm(meta={'csrf': False})
    for sequor in form.sequence.entries:
        sequor.relay.choices = sorted(list(
            (r.id, r.name)
            for r in relays.values()
        ))
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate")
            flash(form.errors)
        else:
            while len(form.sequence.entries) > len(seq.sequence):
                seq.sequence += [Sequor(None, 0)]
            form.populate_obj(seq)
            for sequor in seq.sequence:
                sequor.relay = relays[sequor.relay]
            sequences[sequence_id] = seq
            flash(
                ' '.join(
                    [
                        "Updated",
                        current_app.config["SEQUITUR_NAME"],
                        seq.name + '.',
                    ]
                ), "success"
            )
            return redirect(url_for(".index"))
    return render_template(
        "edit.html",
        title="edit " + current_app.config["SEQUITUR_NAME"],
        describe=" ".join(
            [
                "Change the settings, and",
                "change, move, add, delete entries for",
                current_app.config["SEQUITUR_NAME"],
                seq.name,
                "in the fields below."
            ]
        ),
        subject=current_app.config["SEQUITUR_NAME"],
        fields=fields,
        form=form,
    )


@sequence.route("/delete/<string:sequence_id>/")
@redirected()
def delete(sequence_id):
    del sequences[sequence_id]


@sequence.route("/start/<string:sequence_id>/")
@redirected()
def start(sequence_id):
    sequences[sequence_id].start()


@sequence.route("/stop/<string:sequence_id>/")
@redirected()
def stop(sequence_id: str):
    sequences[sequence_id].stop()
