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
    from util.redirected import redirected
    from util.template import filter_pluralize as pluralize
    relays = Baton()
    boards = Holder()

relay = Blueprint("relay", __name__, url_prefix="/relay")

fields = [
    "name", "description", "active",
    "visible", "default_time", "max_time",
    "board", "index"
]
mappings = ["requires"]
redirected = redirected(relays, current_app.config["RELAY_NAME"], ".index")


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
                    current_app.config["RELAY_NAME"].capitalize(),
                    relays[relay_id].name,
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
    max_relays = current_app.config["MAX_CONCURRENT"]
    interval = int(request.form["minutes"])
    if interval <= relays[relay_id].max_time:
        if len(relays.state()) >= max_relays:
            flash(
                " ".join(
                    [
                        current_app.config["RELAY_NAME"].capitalize(),
                        relays[relay_id].name,
                        "was not turned on for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                        "Maximum number of active",
                        pluralize(current_app.config["RELAY_NAME"]),
                        "(" + str(max_relays) + ") reached."
                    ]
                ),
                "error",
            )
        elif relay_id in relays.keys():
            relays[relay_id].on(timedelta(minutes=interval))
            flash(
                " ".join(
                    [
                        current_app.config["RELAY_NAME"].capitalize(),
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
                    current_app.config["RELAY_NAME"].capitalize(),
                    relays[relay_id].name,
                    "was not turned on for",
                    str(interval),
                    "minute." if interval == 1 else "minutes.",
                    "This exceeds the max interval set for this",
                    current_app.config["RELAY_NAME"],
                    "(" + str(relays[relay_id].max_time),
                    "minute)." if relays[relay_id].max_time == 1 else "minutes)."
                ]
            ),
            "error",
        )
    return redirect(url_for("index"))


@relay.route("/config/")
def index():
    fields = ["name", "description", "address",
              "max_time", "default_time", "visible", "dependencies"]
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=[current_app.config["RELAY_NAME"], "spin_up"],
        data_name="dependencies",
        subject=current_app.config["RELAY_NAME"],
        items={
            id: {
                "fields": {
                    field: relay.__getattribute__(field)
                    for field in fields
                    if field not in ["dependencies", "address"]
                } | {
                    current_app.config["BOARD_NAME"]: relay.board.name,
                    "address": relay.index
                } | {
                    "dependencies": {
                        dep.relay.id: {
                            current_app.config["RELAY_NAME"]: dep.relay.name,
                            "spin_up": dep.spin_up
                        }
                        for dep in relay.requires
                        if relay.requires != []
                    }
                },
                "actions": {
                    "inactive": {
                        "activate": {
                            "name": "activate".capitalize(),
                            "endpoint": ".activate",
                            "args": {"relay_id": id},
                        },
                    },
                    "active": {
                        "deactivate": {
                            "name": "deactivate".capitalize(),
                            "endpoint": ".deactivate",
                            "args": {"relay_id": id},
                        },
                    },
                    "stopped": {
                        "edit": {
                            "name": "edit".capitalize(),
                            "endpoint": ".edit_relay",
                            "args": {"relay_id": id},
                        },
                        "delete": {
                            "name": "delete".capitalize(),
                            "endpoint": ".delete",
                            "args": {"relay_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting",
                                current_app.config["RELAY_NAME"],
                                relay.name,
                                "will delete all",
                                "information on this",
                                current_app.config["RELAY_NAME"],
                                "including its list of dependencies."
                            ]),
                        }
                    },
                    "always": {},
                },
                "active": relay.active,
                "running": relay.timer.is_set(),
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
                        "on",
                        current_app.config["BOARD_NAME"],
                        board.name,
                        "is already assigned to",
                        current_app.config["RELAY_NAME"],
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
                ''.join(
                    [
                        "Dependency list must not contain duplicate ",
                        pluralize(current_app.config["RELAY_NAME"]),
                    ]
                )
            )

        def detect_cycle(target, current=None, visited=None):
            if target == current:
                raise ValidationError("Cyclic dependency graph detected")
            if current is None and visited is None:
                visited = list()
                for d in [
                    d.relay.data for d in field.entries if d.relay.data != '0'
                ]:
                    if d not in visited:
                        visited.append(d)
                        visited = detect_cycle(target, d, visited)
            else:
                for d in relays[current].requires:
                    if d.relay.id not in visited:
                        visited.append(d.relay.id)
                        visited = detect_cycle(target, d.relay.id, visited)
            return visited
        if relay_id in relays.keys():
            dep_graph_order = len(detect_cycle(relay_id))
            if dep_graph_order > 0:
                flash(
                    "Dependency graph order: " + str(dep_graph_order), "append"
                )

    class EditRelayForm(RelayForm):
        index = SelectField('Index', coerce=int, validators=[validate_index])
        requires = FieldList(FormField(DependencyForm),
                             validators=[validate_requires])

    relay = relays[relay_id] if relay_id in relays.keys() else Relay(
        **{
            "id": relay_id,
            "name": ' '.join(
                [
                    current_app.config["RELAY_NAME"].capitalize(),
                    ''.join(choices(ascii_uppercase, k=5)),
                ]
            ),
            "description": "A " + current_app.config["RELAY_NAME"],
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
    form_is_validated = form.validate_on_submit()
    if request.method == "POST" and not form_is_validated:
        flash("Form failed to validate")
        flash(form.errors)
    elif request.method == "POST" and form_is_validated:
        old_board = relay.board
        new_board = boards[form.board.data]
        new_index = False
        if old_board != new_board or relay.index != form.index.data:
            new_index = True
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
        if new_index:
            new_board[relay.index] = relay
        flash(
            ' '.join(
                [
                    "Updated",
                    current_app.config["RELAY_NAME"],
                    relay.name + '.',
                ]
            ), "success"
        )
        return redirect(url_for(".index"))
    return render_template(
        "edit.html",
        title="edit " + current_app.config["RELAY_NAME"],
        describe=" ".join(
            [
                "Change settings for",
                current_app.config["RELAY_NAME"],
                relay.name,
                "and its dependencies in the fields below."
            ]
        ),
        subject=current_app.config["RELAY_NAME"],
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
@redirected()
def delete(relay_id):
    del relays[relay_id]


@relay.route("/config/activate/<string:relay_id>")
@redirected()
def activate(relay_id):
    relays[relay_id].active = True
    relays.save()


@relay.route("/config/deactivate/<string:relay_id>")
@redirected()
def deactivate(relay_id):
    relays[relay_id].active = False
    relays.save()
