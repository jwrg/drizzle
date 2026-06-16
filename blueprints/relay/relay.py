"""
Routes for activating relay timers
"""
from datetime import timedelta
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
    from util.template import (
        filter_pluralize as pluralize,
        filter_capitalize_first as capitalize
    )
    relays = Baton()
    boards = Holder()

relay = Blueprint("relay", __name__, url_prefix="/relay")

fields = ["name", "description", "active", "visible", "board", "index"]
redirected = redirected(relays, current_app.config["RELAY_NAME"], ".index")


@relay.route("/")
def index():
    fields = ["name", "description", "address", "visible", "dependencies"]
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=[current_app.config["RELAY_NAME"], "spin_up"],
        data_name=pluralize(current_app.config["DEPENDENCY_NAME"]),
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
                    pluralize(current_app.config["DEPENDENCY_NAME"]): {
                        dep.relay.id: {
                            current_app.config["RELAY_NAME"]: dep.relay.name,
                            "spin_up": dep.spin_up
                        }
                        for dep in relay.dependencies
                        if relay.dependencies != []
                    }
                },
                "actions": {
                    "inactive": {
                        "activate": {
                            "name": capitalize("activate"),
                            "endpoint": ".activate",
                            "args": {"relay_id": id},
                        },
                    },
                    "active": {
                        "deactivate": {
                            "name": capitalize("deactivate"),
                            "endpoint": ".deactivate",
                            "args": {"relay_id": id},
                        },
                    },
                    "stopped": {
                        "edit": {
                            "name": capitalize("edit"),
                            "endpoint": ".edit",
                            "args": {"relay_id": id},
                        },
                        "delete": {
                            "name": capitalize("delete"),
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
                                "including its list of",
                                pluralize(
                                    current_app.config["DEPENDENCY_NAME"]
                                ) + '.'
                            ]),
                        }
                    },
                    "always": {},
                },
                "active": relay.active,
                "running": relay.counter > 0,
            }
            for id, relay in {
                connection.relay.id: connection.relay
                for board in boards.values()
                for connection in board.addresses
                if connection.relay is not None
            }.items()
        }
    )


@relay.route("/off/<string:relay_id>/", methods=(["POST"]))
def off(relay_id):
    """
    API command for turning off a relay, given its id
    """
    if relay_id in relays.keys():
        relays[relay_id].off(True)
        flash(
            ' '.join(
                [
                    capitalize(current_app.config["RELAY_NAME"]),
                    relays[relay_id].name,
                    "was turned off."
                ]
            ),
            "success"
        )
    else:
        flash(
            ' '.join(
                [
                    "Id", str(relay_id), "not found."
                ]
            ),
            "error",
        )
    return redirect(url_for("index"))


@relay.route("/on/<string:relay_id>/", methods=(["POST"]))
def on(relay_id):
    """
    API command that turns on a relay specified by id for a given
    number of minutes
    """
    max_relays = current_app.config["MAX_CONCURRENT"]
    interval = int(request.form["minutes"])
    if relay_id not in relays.keys():
        flash(
            ' '.join(
                [
                    "Id", str(relay_id), "not found."
                ]
            ),
            "error",
        )
    elif not relays[relay_id].active:
        flash(
            ' '.join(
                [
                    "Relay",
                    str(relays[relay_id].name),
                    "is set as inactive",
                    "and therefore was",
                    "not turned on.",
                ]
            ), "caution"
        )
    elif len(relays.state()) >= max_relays:
        flash(
            ' '.join(
                [
                    capitalize(current_app.config["RELAY_NAME"]),
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
    else:
        relays[relay_id].on(timedelta(minutes=interval))
        flash(
            ' '.join(
                [
                    capitalize(current_app.config["RELAY_NAME"]),
                    relays[relay_id].name,
                    "was turned on for",
                    str(interval),
                    "minute." if interval == 1 else "minutes.",
                ]
            ),
            "success",
        )
    return redirect(url_for("index"))


@relay.route("/new/", methods=(["GET", "POST"]))
def new():
    return redirect(
        url_for(
            ".edit", relay_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@relay.route("/edit/<string:relay_id>/", methods=(["GET", "POST"]))
def edit(relay_id):
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

    def validate_dependencies(form, field):
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
                ' '.join(
                    [
                        capitalize(current_app.config["DEPENDENCY_NAME"]),
                        "list must not contain duplicate",
                        pluralize(current_app.config["RELAY_NAME"]) + '.'
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
                for d in relays[current].dependencies:
                    if d.relay.id not in visited:
                        visited.append(d.relay.id)
                        visited = detect_cycle(target, d.relay.id, visited)
            return visited
        if relay_id in relays.keys():
            dep_graph_order = len(detect_cycle(relay_id))
            if dep_graph_order > 0:
                flash(
                    "Dependency graph order: " + str(dep_graph_order),
                    "append"
                )

    class EditRelayForm(RelayForm):
        index = SelectField('Index', coerce=int, validators=[validate_index])
        dependencies = FieldList(FormField(DependencyForm),
                                 validators=[validate_dependencies])

    relay = relays[relay_id] if relay_id in relays.keys() else Relay(
        **{
            "id": relay_id,
            "name": ' '.join(
                [
                    capitalize(current_app.config["RELAY_NAME"]),
                    ''.join(choices(ascii_uppercase, k=5)),
                ]
            ),
            "description": "A " + current_app.config["RELAY_NAME"],
            "active": True,
            "visible": True,
            "board": 0,
            "index": 0,
            "dependencies": [],
        }
    )

    if request.method == "GET":
        if len(relay.dependencies) == 0:
            relay.dependencies += [Dependency(**{"relay": "0", "spin_up": 0})]
        form = EditRelayForm(
            formdata=None,
            obj=relay,
            meta={'csrf': False},
        )
        relay.dependencies = [d for d in relay.dependencies if d.relay != '0']
    else:
        form = EditRelayForm(meta={'csrf': False})
    form.board.choices = [
        (board.id, board.name)
        for board in boards.values()
    ]
    form.index.choices = [
        (index, index) for index in range(1, 8)
    ]
    for entry in form.dependencies.entries:
        entry.relay.choices = [
            ('0', "Choose a dependency if required...")
        ] + sorted(list(
            (r.id, r.name)
            for r in relays.values()
            if r is not relay
        ))
    form_is_validated = form.validate_on_submit()
    if request.method == "POST" and not form_is_validated:
        flash("Form failed to validate: " + str(form.errors), "error")
    elif request.method == "POST" and form_is_validated:
        old_board = relay.board
        new_board = boards[form.board.data]
        new_index = False
        if old_board != new_board or relay.index != form.index.data:
            new_index = True
            if relay.index != 0:
                del old_board[relay.index]
        while len(form.dependencies.entries) > len(relay.dependencies):
            relay.dependencies += [Dependency(None, 0)]
        form.populate_obj(relay)
        relay.dependencies = [d for d in relay.dependencies if d.relay != '0']
        relay.board = boards[relay.board]
        for dep in relay.dependencies:
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
        data_name=current_app.config["DEPENDENCY_NAME"],
        subject=current_app.config["RELAY_NAME"],
        fields=[
            "name",
            "description",
            "active",
            "visible",
            "board",
            "index",
            "dependencies"
        ],
        form=form,
        max_rows=len(relays)
    )


@relay.route("/delete/<string:relay_id>")
@redirected()
def delete(relay_id):
    del relays[relay_id]


@relay.route("/activate/<string:relay_id>")
@redirected()
def activate(relay_id):
    relays[relay_id].active = True
    relays.save()


@relay.route("/deactivate/<string:relay_id>")
@redirected()
def deactivate(relay_id):
    if relays[relay_id].counter > 0:
        flash(
            "Cannot deactivate a currently running " +
            current_app.config["RELAY_NAME"],
            "caution"
        )
    else:
        relays[relay_id].active = False
        relays.save()
