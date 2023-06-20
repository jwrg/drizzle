"""
Routes for sequencing relays
"""
from re import match
from time import strftime

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
    from util.jsonny import Jsonny
    from util.sequencer import Sequencer
sequence = Blueprint("sequence", __name__, url_prefix="/sequence")


@sequence.route("/")
def list_sequences():
    """
    View that lists all available sequences
    """
    actions = {
        "run": "sequence.run_sequence",
        "edit": "sequence.edit_sequence",
        "delete": "sequence.delete_sequence",
    }
    active = {"stop": "sequence.stop_sequence"}
    fields = ["name", "description", "sequence"]
    items = []
    for sequence_id, entry in Jsonny.get("sequences").items():
        new_item = [sequence_id]
        new_item.append({field: entry[field] for field in fields})
        if sequence_id == str(Sequencer.sequence):
            new_item.append(
                [(key.capitalize(), value, {}, True) for key, value in active.items()]
            )
            new_item.append(True)
        else:
            new_item.append(
                [
                    (key.capitalize(), value, {"sequence_id": sequence_id}, True)
                    for key, value in actions.items()
                ]
            )
            new_item.append(False)
        items.append(new_item)
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=["zone", "minutes"],
        data_name="sequence",
        subject="sequence",
        items=items,
    )


@sequence.route("/run/<int:sequence_id>/")
def run_sequence(sequence_id):
    """
    API command that executes a sequence, given its id number
    """
    sequences = Jsonny.get("sequences")
    if Sequencer.sequence is None:
        Sequencer.init_sequence(sequence_id)
        flash(
            " ".join(
                [
                    "Sequence",
                    sequences[str(sequence_id)]["name"],
                    "started.",
                ]
            ),
            "success",
        )
    else:
        flash(
            " ".join(
                [
                    "Sequence",
                    sequences[str(sequence_id)]["name"],
                    "NOT started. Sequence",
                    sequences[str(Sequencer.sequence)]["name"],
                    "currently running.",
                ]
            )
        )
    return redirect(url_for(".list_sequences"))


@sequence.route("/stop/")
def stop_sequence():
    """
    API command that stops any currently active sequence
    """
    Sequencer.cancel_sequence()
    flash("Sequence cancelled.", "caution")
    return redirect(url_for(".list_sequences"))


@sequence.route("/new/", methods=("GET", "POST"))
def new_sequence():
    """
    View that creates a new sequence
    """
    sequence_id = str(max(int(x) for x in Jsonny.get("sequences").keys()) + 1)
    if request.method == "POST":
        return redirect(url_for(".edit_sequence", sequence_id=sequence_id), code=307)
    return render_template(
        "edit.html",
        id=sequence_id,
        subject="sequence",
        item={
            "name": "",
            "description": "",
            "sequence": {
                "0": {"zone": 1, "minutes": 1},
                "columns": ["zone", "minutes"],
            },
        },
        fields=["name", "description", "sequence"],
        data_headings=["zone", "minutes"],
        constrain={
            "minutes": 120,
            "zone": {
                str(x): "Zone " + str(x)
                for x in list(range(1, Platelet.num_zones + 1))
            },
        },
        num_zones=Platelet.num_zones,
    )


@sequence.route("/edit/<int:sequence_id>/", methods=("GET", "POST"))
def edit_sequence(sequence_id):
    """
    View that edits a sequence, given its id number
    """
    if request.method == "POST":
        sequences = Jsonny.get("sequences")
        fields = ["description", "name"]
        resultant = {}
        resultant["created"] = (
            strftime("%Y-%m-%dT%H:%M:%S.999Z")
            if str(sequence_id) not in sequences
            else sequences[str(sequence_id)]["created"]
        )
        for field in fields:
            if request.form[field] == "":
                resultant[field] = field
            else:
                resultant[field] = request.form[field]
        resultant["modified"] = strftime("%Y-%m-%dT%H:%M:%S.999Z")
        resultant["sequence"] = {
            str(p): {"zone": q, "minutes": r}
            for p, (q, r) in enumerate(
                list(
                    zip(
                        [
                            int(request.form.get(y))
                            for y in [
                                z for z in request.form.keys() if match("zone-*", z)
                            ]
                        ],
                        [
                            int(request.form.get(y))
                            for y in [
                                z for z in request.form.keys() if match("minutes-*", z)
                            ]
                        ],
                    )
                )
            )
        }
        resultant["sequence"]["columns"] = ["zone", "minutes"]
        sequences.update({str(sequence_id): resultant})
        Jsonny.put("sequences", sequences)
        flash(" ".join(["Sequence", resultant["name"], "updated."]), "success")
        return redirect(url_for(".list_sequences"))
    return render_template(
        "edit.html",
        id=str(sequence_id),
        subject="sequence",
        item=Jsonny.get("sequences")[str(sequence_id)],
        fields=["name", "description", "sequence"],
        data_headings=["zone", "minutes"],
        constrain={
            "minutes": Platelet.max_minutes,
            "zone": {
                x: "Zone " + str(x)
                for x in list(range(1, Platelet.num_zones + 1))
            },
        },
        num_zones=Platelet.num_zones,
    )


@sequence.route("/delete/<int:sequence_id>/")
def delete_sequence(sequence_id):
    """
    API command that deletes a sequence, given its id number
    """
    sequences = Jsonny.get("sequences")
    removed = sequences.pop(str(sequence_id))
    Jsonny.put("sequences", sequences)
    flash(" ".join(["Sequence", removed["name"], "deleted."]), "caution")
    return redirect(url_for(".list_sequences"))
