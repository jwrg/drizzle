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
    relays = Baton()
    sequences = Sequencer()
sequence = Blueprint("sequence", __name__, url_prefix="/sequence")

fields = ["name", "description", "sequence"]


@sequence.route("/")
def list_sequences():
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=["index", "relay", "minutes"],
        data_name="sequence",
        subject="sequence",
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
                            "relay": entry.relay.name,
                            "minutes": str(entry.minutes)
                        }
                        for ordinal, entry in enumerate(seq.sequence)
                    }
                },
                "actions": {
                    "inactive": {
                        "run": {
                            "name": "run".capitalize(),
                            "endpoint": ".run_sequence",
                            "args": {"sequence_id": id},
                        },
                        "edit": {
                            "name": "edit".capitalize(),
                            "endpoint": ".edit_sequence",
                            "args": {"sequence_id": id},
                        },
                        "delete": {
                            "name": "delete".capitalize(),
                            "endpoint": ".delete_sequence",
                            "args": {"sequence_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting",
                                seq.name,
                                "cannot be undone.",
                            ]),
                        }
                    },
                    "active": {
                        "stop": {
                            "name": "stop".capitalize(),
                            "endpoint": ".stop_sequence",
                            "args": {"sequence_id": id},
                        },
                    },
                    "always": {
                    },
                },
                "active": seq.active
            }
            for id, seq in sequences.items()
        }
    )


@sequence.route("/run/<string:sequence_id>/")
def run_sequence(sequence_id):
    if sequence_id in sequences.keys():
        sequences[sequence_id].start()
        flash(
            " ".join(
                [
                    "Sequence",
                    sequences[str(sequence_id)].name,
                    "started.",
                ]
            ),
            "success",
        )
    else:
        flash(
            " ".join(
                [
                    "Sequence id",
                    str(sequence_id),
                    "not found.",
                ]
            )
        )
    return redirect(url_for(".list_sequences"))


@sequence.route("/stop/<string:sequence_id>/")
def stop_sequence(sequence_id: str):
    if sequence_id in sequences.keys():
        sequences[sequence_id].stop()
        flash(
            " ".join(
                [
                    "Sequence",
                    sequences[str(sequence_id)].name,
                    "stopped.",
                ]
            ),
            "success",
        )
    else:
        flash(
            " ".join(
                [
                    "Sequence id",
                    str(sequence_id),
                    "not found.",
                ]
            )
        )
    return redirect(url_for(".list_sequences"))


@sequence.route("/new/", methods=("GET", "POST"))
def new_sequence():
    return redirect(
        url_for(
            ".edit_sequence", sequence_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@sequence.route("/edit/<string:sequence_id>/", methods=("GET", "POST"))
def edit_sequence(sequence_id):
    seq = sequences[sequence_id] if sequence_id in sequences.keys(
    ) else Sequitur(
        **{
            "id": sequence_id,
            "name": "New relay sequence" + ''.join(choices(ascii_uppercase, k=5)),
            "description": "A sequence of relays and durations",
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
    if request.method == "POST" and not form.validate_on_submit():
        flash("Form failed to validate")
        flash(form.errors)
    elif request.method == "POST" and form.validate_on_submit():
        while len(form.sequence.entries) > len(seq.sequence):
            seq.sequence += [Sequor(None, 0)]
        form.populate_obj(seq)
        for sequor in seq.sequence:
            sequor.relay = relays[sequor.relay]
        sequences[sequence_id] = seq
        flash("Updated sequence " + seq.name, "success")
        return redirect(url_for(".list_sequences"))
    return render_template(
        "edit.html",
        title="edit sequence",
        describe=" ".join(
            [
                "change the settings, and",
                "change, move, add, delete entries",
                "for sequence",
                seq.name,
                "in the fields below."
            ]
        ),
        subject="sequence",
        fields=fields,
        form=form,
    )


@sequence.route("/delete/<string:sequence_id>/")
def delete_sequence(sequence_id):
    if sequence_id in sequences.keys():
        flash(
            " ".join(
                [
                    "Sequence",
                    sequences[str(sequence_id)].name,
                    "deleted.",
                ]
            ),
            "success",
        )
        del sequences[sequence_id]
    else:
        flash(
            " ".join(
                [
                    "Sequence id",
                    str(sequence_id),
                    "not found.",
                ]
            ),
            "caution",
        )
    return redirect(url_for(".list_sequences"))
