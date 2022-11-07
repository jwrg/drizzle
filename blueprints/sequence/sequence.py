from time import strftime
from json import dump, load
from re import match
from flask import (
    Blueprint,
    current_app,
    flash,
    render_template,
    redirect,
    request,
    url_for,
)

with current_app.app_context():
    from util.Sequencer import Sequencer
sequence = Blueprint("sequence", __name__, url_prefix="/sequence")


@sequence.route("/")
def list():
    actions = {
        "run": "sequence.runSequence",
        "edit": "sequence.editSequence",
        "delete": "sequence.deleteSequence",
    }
    active = {"stop": "sequence.stopSequence"}
    fields = ["name", "description", "sequence"]
    items = []
    for id, entry in Sequencer.getSequences().items():
        new_item = [id]
        new_item.append({field: entry[field] for field in fields})
        if id == str(Sequencer.sequence):
            new_item.append(
                [(key.capitalize(), value, {}, True) for key, value in active.items()]
            )
            new_item.append(True)
        else:
            new_item.append(
                [
                    (key.capitalize(), value, {"id": id}, True)
                    for key, value in actions.items()
                ]
            )
            new_item.append(False)
        items.append(new_item)
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=["zone", "minutes"],
        subject="sequence",
        items=items,
    )


@sequence.route("/run/<int:id>/")
def runSequence(id):
    Sequencer.initSequence(id)
    flash(
        " ".join(["Sequence", Sequencer.getSequences()[str(id)]["name"], "started."]),
        "success",
    )
    return redirect(url_for(".list"))


@sequence.route("/stop/")
def stopSequence():
    Sequencer.cancelSequence()
    flash("Sequence cancelled.", "caution")
    return redirect(url_for(".list"))


@sequence.route("/new/", methods=("GET", "POST"))
def newSequence():
    id = str(max([int(x) for x in Sequencer.getSequences().keys()]) + 1)
    if request.method == "POST":
        return redirect(url_for(".editSequence", id=id), code=307)
    return render_template(
        "edit.html",
        id=id,
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
        constrain={
            "minutes": 120,
            "zone": [x for x in range(1, current_app.config["NUM_ZONES"] + 1)],
        },
        num_zones=current_app.config["NUM_ZONES"],
    )


@sequence.route("/edit/<int:id>/", methods=("GET", "POST"))
def editSequence(id):
    if request.method == "POST":
        sequences = Sequencer.getSequences()
        fields = ["description", "name"]
        resultant = {}
        resultant["created"] = (
            strftime("%Y-%m-%dT%H:%M:%S.999Z")
            if str(id) not in sequences
            else sequences[str(id)]["created"]
        )
        for field in fields:
            if request.form[field] == "":
                resultant[field] = field
            else:
                resultant[field] = request.form[field]
        resultant["modified"] = strftime("%Y-%m-%dT%H:%M:%S.999Z")
        resultant["sequence"] = {
            str(x): {"zone": y, "minutes": z}
            for x, (y, z) in enumerate(
                [
                    x
                    for x in zip(
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
                ]
            )
        }
        resultant["sequence"]["columns"] = ["zone", "minutes"]
        sequences.update({str(id): resultant})
        Sequencer.putSequences(sequences)
        flash(" ".join(["Sequence", resultant["name"], "updated."]), "success")
        return redirect(url_for(".list"))
    return render_template(
        "edit.html",
        id=str(id),
        subject="sequence",
        item=Sequencer.getSequences()[str(id)],
        fields=["name", "description", "sequence"],
        constrain={
            "minutes": current_app.config["MAX_TIME"],
            "zone": [x for x in range(1, current_app.config["NUM_ZONES"] + 1)],
        },
        num_zones=current_app.config["NUM_ZONES"],
    )


@sequence.route("/delete/<int:id>/")
def deleteSequence(id):
    sequences = Sequencer.getSequences()
    removed = sequences.pop(str(id))
    Sequencer.putSequences(sequences)
    flash(" ".join(["Sequence", removed["name"], "deleted."]), "caution")
    return redirect(url_for(".list"))
