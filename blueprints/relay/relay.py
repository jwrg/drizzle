"""
Routes for activating relay timers
"""
from datetime import timedelta, datetime
from random import choices
from string import ascii_uppercase, ascii_lowercase, digits

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for
)
from wtforms import SelectField, FieldList, FormField
from wtforms.validators import ValidationError

with current_app.app_context():
    from util.board import Holder
    from util.relay import Baton, Relay, Dependency
    from util.form import RelayForm, DependencyForm
    relays = Baton()
    boards = Holder()

relay = Blueprint("relay", __name__, url_prefix="/relay")

fields = [
    "name", "description", "active",
    "visible", "default_time", "max_time",
    "board", "index"
]
mappings = ["requires"]


@relay.route("/")
def select_relay():
    """
    View that selects the relay to activate
    """
    state = relays.state()
    return render_template(
        "keypad.html",
        subject="dashboard",
        actions=[
            (
                relay.name,
                "deactivate" if id in state.keys() else "activate",
                "relay.disable_relay" if id in state.keys() else "relay.enable_relay",
                {"relay_id": id},
                True,
                id in state.keys(),
                state[id] if id in state.keys() else None,
                relay.default_time,
                relay.max_time,
            )
            for id, relay in relays.items()
        ],
        datetime=datetime.now().strftime("%d/%m/%y %H:%M:%S"),
        times=[1, 2, 5, 10, 20, 30]
    )


@relay.route("/disable/<string:relay_id>/", methods=(["POST"]))
def disable_relay(relay_id):
    """
    API command for turning off a relay, given its id
    """
    if relay_id in relays.keys():
        relays[relay_id].off()
        flash(
            " ".join(
                [
                    "Relay", relays[relay_id].name,
                    "was turned off."
                ]
            ),
            "success"
        )
    else:
        flash(
            " ".join(
                [
                    "Id", str(relay_id), "not found."
                ]
            ),
            "caution",
        )
    return redirect(url_for("index"))


@relay.route("/enable/<string:relay_id>/", methods=(["POST"]))
def enable_relay(relay_id):
    """
    API command that activates a relay specified by id for a given number of minutes
    """
    with current_app.app_context():
        max_relays = current_app.config["MAX_CONCURRENT"]
    interval = int(request.form["minutes"])
    if interval <= relays[relay_id].max_time:
        if len(relays.state()) >= max_relays:
            flash(
                " ".join(
                    [
                        "Relay",
                        relays[relay_id].name,
                        "was not turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                        "Maximum number of active relays (",
                        str(max_relays),
                        ") reached."
                    ]
                ),
                "error",
            )
        elif relay_id in relays.keys():
            relays[relay_id].on(timedelta(minutes=interval))
            flash(
                " ".join(
                    [
                        "Relay",
                        relays[relay_id].name,
                        "was turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                    ]
                ),
                "success",
            )
        else:
            flash(
                " ".join(
                    [
                        "Id", str(relay_id), "not found."
                    ]
                ),
                "caution",
            )
    else:
        flash(
            " ".join(
                [
                    "Relay",
                    relays[relay_id].name,
                    "was not turned on for",
                    str(interval),
                    "minute." if interval == 1 else "minutes.",
                    "This exceeds the max interval set for this relay (",
                    str(relays[relay_id].max_time),
                    "minute)." if relays[relay_id].max_time == 1 else "minutes)."
                ]
            ),
            "error",
        )
    return redirect(url_for("index"))


@relay.route("/config/")
def list_relays():
    fields = ["name", "description", "address",
              "max_time", "default_time", "visible", "requires"]
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=["relay", "spin_up"],
        data_name="requires",
        subject="relay",
        items={
            id: {
                "fields": {
                    field: relay.__getattribute__(field)
                    for field in fields
                    if field not in ["requires", "address"]
                } | {
                    "board": relay.board.name,
                    "address": relay.index
                } | {
                    "requires": {
                        dep.relay.id: {"relay": dep.relay.name,
                                       "spin_up": dep.spin_up}
                        for dep in relay.requires
                        if relay.requires != []
                    }
                },
                "actions": {
                    "inactive": {
                        "activate": {
                            "name": "activate".capitalize(),
                            "endpoint": ".activate_relay",
                            "args": {"relay_id": id},
                        },
                    },
                    "active": {
                        "deactivate": {
                            "name": "deactivate".capitalize(),
                            "endpoint": ".deactivate_relay",
                            "args": {"relay_id": id},
                        },
                    },
                    "always": {
                        "edit": {
                            "name": "edit".capitalize(),
                            "endpoint": ".edit_relay",
                            "args": {"relay_id": id},
                        },
                        "delete": {
                            "name": "delete".capitalize(),
                            "endpoint": "relay.delete_relay",
                            "args": {"relay_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting relay",
                                relay.name,
                                "will delete all",
                                "information on this relay",
                                "including its list of dependencies."
                            ]),
                        }
                    },
                },
                "active": relay.active
            }
            for id, relay in {
                connection.relay.id: connection.relay
                for board in boards.values()
                for connection in board.addresses
                if connection.relay is not None
            }.items()
        }
    )


@relay.route("/config/new/", methods=(["GET", "POST"]))
def new_relay():
    return redirect(
        url_for(
            ".edit_relay", relay_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@relay.route("/config/activate/<string:relay_id>")
def activate_relay(relay_id):
    relays[relay_id].active = True
    relays.save()
    flash("Relay " + relays[relay_id].name + " is now set as active.")
    return redirect(url_for(".list_relays"))


@relay.route("/config/deactivate/<string:relay_id>")
def deactivate_relay(relay_id):
    relays[relay_id].active = False
    relays.save()
    flash(
        "Relay " + relays[relay_id].name + " is now set as inactive."
    )
    return redirect(url_for(".list_relays"))


@relay.route("/config/edit/<string:relay_id>/", methods=(["GET", "POST"]))
def edit_relay(relay_id):
    def validate_index(form, field):
        board = boards[form.board.data]
        if (
            relay_id not in relays.keys() or
            form.board.data != relay.board.id or
            form.index.data != relay.index
        ) and form.index.data not in board.get_open_addresses():
            raise ValidationError(
                ' '.join(
                    [
                        "Address with index",
                        str(field.data),
                        "on board",
                        board.name,
                        "is already assigned to relay",
                        board[form.index.data].name,
                    ]
                )
            )

    def validate_requires(form, field):
        if len(
            [
                d.relay.data for d in field.entries
                if d.relay.data != '0'
            ]
        ) > len(
            {
                d.relay.data for d in field.entries
                if d.relay.data != '0'
            }
        ):
            raise ValidationError(
                "Dependency list must not contain duplicate relays."
            )

    class EditRelayForm(RelayForm):
        index = SelectField('Index', coerce=int, validators=[validate_index])
        requires = FieldList(FormField(DependencyForm),
                             validators=[validate_requires])

    relay = relays[relay_id] if relay_id in relays.keys() else Relay(
        **{
            "id": relay_id,
        } | {

            "name": "New Relay " + ''.join(choices(ascii_uppercase + digits, k=5)),
            "description": "",
            "active": True,
            "visible": True,
            "default_time": 10,
            "max_time": 60,
            "board": 0,
            "index": 0,
            "requires": [],
        }
    )

    if request.method == "GET":
        if len(relay.requires) == 0:
            relay.requires += [Dependency(**{"relay": "0", "spin_up": 0})]
        form = EditRelayForm(
            formdata=None,
            obj=relay,
            meta={'csrf': False},
        )
        relay.requires = [d for d in relay.requires if d.relay != '0']
    else:
        form = EditRelayForm(meta={'csrf': False})
    form.board.choices = [
        (board.id, board.name)
        for board in boards.values()
    ]
    form.index.choices = [
        (index, index) for index in range(1, 8)
    ]
    for entry in form.requires.entries:
        entry.relay.choices = [
            ('0', "Choose a dependency if required...")
        ] + sorted(list(
            (r.id, r.name)
            for r in relays.values()
            if r is not relay
        ))
    if request.method == "POST" and not form.validate_on_submit():
        flash("Form failed to validate")
        flash(form.errors)
    elif request.method == "POST" and form.validate_on_submit():
        old_board = relay.board
        new_board = boards[form.board.data]
        del new_board[relay.index]
        if relay.index != 0:
            del old_board[relay.index]
        while len(form.requires.entries) > len(relay.requires):
            relay.requires += [Dependency(None, 0)]
        form.populate_obj(relay)
        relay.requires = [d for d in relay.requires if d.relay != '0']
        relay.board = boards[relay.board]
        for dep in relay.requires:
            if dep.relay != '0':
                dep.relay = relays[dep.relay]
        relays[relay_id] = relay
        new_board[relay.index] = relay
        flash("Updated relay " + relay.name + " .")
        return redirect(url_for(".list_relays"))
    return render_template(
        "edit.html",
        title="edit relay configuration",
        describe=" ".join(
            [
                "change settings for relay",
                relay.name,
                "and its dependencies in the fields below."
            ]
        ),
        subject="relay",
        fields=[
            "name",
            "description",
            "active",
            "visible",
            "default_time",
            "max_time",
            "board",
            "index",
            "requires"
        ],
        form=form,
        max_rows=len(relays)
    )


@relay.route("/config/delete/<string:relay_id>")
def delete_relay(relay_id):
    if relay_id in relays.keys():
        flash(
            " ".join(
                [
                    "Relay",
                    relays[str(relay_id)].name,
                    "deleted.",
                ]
            ),
            "success",
        )
        del relays[relay_id]
    else:
        flash(
            " ".join(
                [
                    "relay id",
                    str(relay_id),
                    "not found.",
                ]
            ),
            "caution",
        )
    return redirect(url_for(".list_relays"))
