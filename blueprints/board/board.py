"""
Routes for configuring connected relay boards
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
    url_for
)

with current_app.app_context():
    from lib.board import Board, Holder
    from util.form import BoardForm
    from util.redirected import redirected
    from util.template import (
        filter_capitalize_first as capitalize,
        filter_pluralize as pluralize
    )
    boards = Holder()

board = Blueprint("board", __name__, url_prefix="/board")

fields = ["name", "description", "type", "index", "active"]
redirected = redirected(boards, current_app.config["BOARD_NAME"], ".index")


@board.route("/")
def index():
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=[current_app.config["RELAY_NAME"], "address"],
        data_name=pluralize(current_app.config["CONNECTION_NAME"]),
        subject=current_app.config["BOARD_NAME"],
        items={
            id: {
                "fields": {
                    field: board.__getattribute__(field)
                    for field in fields
                } | {
                    pluralize(current_app.config["CONNECTION_NAME"]): {
                        conn.relay.id: {
                            current_app.config["RELAY_NAME"]: conn.relay.name,
                            "address": conn.index
                        }
                        for conn in board.addresses
                        if conn.relay is not None
                    }
                },
                "actions": {
                    "inactive": {
                        # "activate": {
                        #     "name": capitalize("activate"),
                        #     "endpoint": ".activate",
                        #     "args": {"board_id": id},
                        # },
                    },
                    "active": {
                        # "deactivate": {
                        #     "name": capitalize("deactivate"),
                        #     "endpoint": ".deactivate",
                        #     "args": {"board_id": id},
                        # },
                    },
                    "always": {
                        "edit": {
                            "name": capitalize("edit"),
                            "endpoint": ".edit",
                            "args": {"board_id": id},
                        },
                        "delete": {
                            "name": capitalize("delete"),
                            "endpoint": ".delete",
                            "args": {"board_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting",
                                current_app.config["BOARD_NAME"],
                                '"' + board.name + '"',
                                "will also delete all the",
                                pluralize(current_app.config["RELAY_NAME"]),
                                "listed as its",
                                pluralize(
                                    current_app.config["CONNECTION_NAME"]
                                ) + "."
                            ]),
                        }
                    },
                },
                "active": board.active
            }
            for id, board in boards.items()
        }
    )


@board.route("/new/")
def new():
    return redirect(
        url_for(
            ".edit", board_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@board.route("/edit/<string:board_id>/", methods=(["GET", "POST"]))
def edit(board_id: str):
    board = boards[board_id] if board_id in boards.keys(
    ) else Board(
        **{
            "id": board_id
        } | {
            "name": ' '.join(
                [
                    current_app.config["BOARD_NAME"],
                    ''.join(choices(ascii_uppercase, k=5)),
                ]
            ),
            "description": "A " + current_app.config["BOARD_NAME"],
            "index": min(
                [
                    x for x in range(0, 8)
                    if x not in [
                        int(y.index) for y in boards.values()
                    ]
                ]
            ),
            "type": "PiPlates",
            "active": True,
        }
    )
    if request.method == "GET":
        form = BoardForm(formdata=None, obj=board, meta={'csrf': False})
    else:
        form = BoardForm(meta={'csrf': False})
    form.index.choices = sorted(list({
        (board.index, board.index)
    } | {
        (index, index) for index in range(0, 7)
        if index not in [
            board.index for board in boards.values()
        ]
    }), key=lambda x: x[0])
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Form failed to validate: " + str(form.errors), "error")
        else:
            form.populate_obj(board)
            boards[board_id] = board
            flash(
                ' '.join(
                    [
                        "Updated",
                        current_app.config["BOARD_NAME"],
                        '"' + board.name + '"',
                    ]
                ), "success"
            )
            return redirect(url_for(".index"))
    return render_template(
        "edit.html",
        title=' '.join(
            [
                "edit",
                current_app.config["BOARD_NAME"],
                '"' + board.name + '"'
            ]
        ),
        describe=' '.join(
            [
                "Change settings for",
                current_app.config["BOARD_NAME"],
                '"' + board.name + '"',
                "in the fields below."
            ]
        ),
        subject=current_app.config["BOARD_NAME"],
        fields=fields,
        allow_reorder=False,
        form=form,
    )


@board.route("/delete/<string:board_id>/")
@redirected()
def delete(board_id: str):
    del boards[board_id]


@board.route("/activate/<string:board_id>")
@redirected()
def activate(board_id: str):
    boards[board_id].active = True
    boards.save()


@board.route("/deactivate/<string:board_id>")
@redirected()
def deactivate(board_id: str):
    boards[board_id].active = False
    boards.save()
