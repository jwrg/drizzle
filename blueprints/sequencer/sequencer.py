"""
Routes for sequencing relays
"""
from random import choices
from operator import itemgetter
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
    from util.template import (
        filter_capitalize_first as capitalize,
        filter_pluralize as pluralize
    )
    relays = Baton()
    sequences = Sequencer()
sequencer = Blueprint("sequencer", __name__, url_prefix="/sequencer")

fields = ["name", "description", "sequencia"]
redirected = redirected(
    sequences,
    current_app.config["SEQUITUR_NAME"],
    "index"
)


@sequencer.route("/")
def index():
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=["index", current_app.config["RELAY_NAME"], "minutes"],
        data_name=pluralize(current_app.config["SEQUENCIA_NAME"]),
        subject=current_app.config["SEQUITUR_NAME"],
        items={
            id: {
                "fields": {
                    field: seq.__getattribute__(field)
                    for field in fields
                    if field != "sequencia"
                } | {
                    pluralize(current_app.config["SEQUENCIA_NAME"]): {
                        ordinal: {
                            "index": int(ordinal) + 1,
                            current_app.config["RELAY_NAME"]: entry.relay.name,
                            "minutes": str(entry.minutes)
                        }
                        for ordinal, entry in enumerate(seq.sequencia)
                    }
                },
                "actions": {
                    "stopped": {
                        "start": {
                            "name": capitalize("start"),
                            "endpoint": ".start",
                            "args": {"sequence_id": id},
                        },
                        "edit": {
                            "name": capitalize("edit"),
                            "endpoint": ".edit",
                            "args": {"sequence_id": id},
                        },
                        "delete": {
                            "name": capitalize("delete"),
                            "endpoint": ".delete",
                            "args": {"sequence_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting",
                                '"' + seq.name + '"',
                                "cannot be undone.",
                            ]),
                        }
                    },
                    "running": {
                        "stop": {
                            "name": capitalize("stop"),
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


@sequencer.route("/new/", methods=("GET", "POST"))
def new():
    return redirect(
        url_for(
            ".edit", sequence_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@sequencer.route("/edit/<string:sequence_id>/", methods=("GET", "POST"))
def edit(sequence_id):
    sequitur = sequences[sequence_id] if sequence_id in sequences.keys(
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
            "sequencia": [Sequor(str(next(iter(relays.values()))), 1)]
        }
    )
    if request.method == "GET":
        form = SequiturForm(formdata=None, obj=sequitur, meta={'csrf': False})
    else:
        form = SequiturForm(meta={'csrf': False})
    for sequor in form.sequencia.entries:
        sequor.relay.choices = sorted(
            list(
                (r.id, r.name)
                for r in relays.values()
            ),
            key=itemgetter(1)
        )
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate: " + str(form.errors), "error")
        else:
            while len(form.sequencia.entries) > len(sequitur.sequencia):
                sequitur.sequencia += [Sequor(None, 0)]
            form.populate_obj(sequitur)
            for sequor in sequitur.sequencia:
                sequor.relay = relays[sequor.relay]
            sequences[sequence_id] = sequitur
            flash(
                ' '.join(
                    [
                        "Updated",
                        current_app.config["SEQUITUR_NAME"],
                        '"' + sequitur.name + '".',
                    ]
                ), "success"
            )
            return redirect(url_for(".index"))
    return render_template(
        "edit.html",
        title=' '.join(
            [
                "edit",
                current_app.config["SEQUITUR_NAME"],
                '"' + sequitur.name + '"'

            ]
        ),
        describe=' '.join(
            [
                "Change the settings, and",
                "change, move, add, delete entries for",
                current_app.config["SEQUITUR_NAME"],
                '"' + sequitur.name + '"',
                "in the fields below."
            ]
        ),
        data_name=current_app.config["SEQUENCIA_NAME"],
        subject=current_app.config["SEQUITUR_NAME"],
        fields=fields,
        allow_reorder=True,
        form=form,
    )


@sequencer.route("/delete/<string:sequence_id>/")
@redirected()
def delete(sequence_id):
    del sequences[sequence_id]


@sequencer.route("/start/<string:sequence_id>/")
@redirected()
def start(sequence_id):
    sequences[sequence_id].start()


@sequencer.route("/stop/<string:sequence_id>/")
@redirected()
def stop(sequence_id: str):
    sequences[sequence_id].stop()
