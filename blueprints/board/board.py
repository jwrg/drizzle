"""
Routes for configuring connected relay boards
"""
from datetime import timedelta, datetime
from random import choices
from re import match
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
    from util.board import Board, Holder
    from util.form import BoardForm
    boards = Holder()

board = Blueprint("board", __name__, url_prefix="/board")

fields = ["name", "description", "type", "index", "active"]


@board.route("/")
def list_boards():
    return render_template(
        "list.html",
        allow_create=True,
        data_headings=["relay", "address"],
        data_name="connections",
        subject="board",
        items={
            id: {
                "fields": {
                    field: board.__getattribute__(field)
                    for field in fields
                } | {
                    "connections": {
                        conn.relay.id: {
                            "relay": conn.relay.name,
                            "address": conn.index
                        }
                        for conn in board.addresses
                        if conn.relay is not None
                    }
                },
                "actions": {
                    "inactive": {
                        "activate": {
                            "name": "activate".capitalize(),
                            "endpoint": ".activate_board",
                            "args": {"board_id": id},
                        },
                    },
                    "active": {
                        "deactivate": {
                            "name": "deactivate".capitalize(),
                            "endpoint": ".deactivate_board",
                            "args": {"board_id": id},
                        },
                    },
                    "always": {
                        "edit": {
                            "name": "edit".capitalize(),
                            "endpoint": ".edit_board",
                            "args": {"board_id": id},
                        },
                        "delete": {
                            "name": "delete".capitalize(),
                            "endpoint": ".delete_board",
                            "args": {"board_id": id},
                            "confirm": ' '.join([
                                "Are you sure?",
                                "Deleting board",
                                board.name,
                                "will also delete all",
                                "the relays listed",
                                "as its connections."
                            ]),
                        }
                    },
                },
                "active": board.active
            }
            for id, board in boards.items()
        }
    )


@board.route("/edit/<string:board_id>/", methods=(["GET", "POST"]))
def edit_board(board_id: str):
    board = boards[board_id] if board_id in boards.keys(
    ) else Board(
        **{
            "id": board_id
        } | {
            "name": "New PiPlates Relay Board",
            "description": "An attached PiPlates relay board",
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
            flash("Form failed to validate", "error")
            flash(form.errors, "error")
        else:
            form.populate_obj(board)
            boards[board_id] = board
            flash("Updated board " + board.name, "success")
            return redirect(url_for(".list_boards"))
    return render_template(
        "edit.html",
        title="edit board configuration",
        describe=" ".join(
            [
                "change the settings for board",
                board.name,
                "in the fields below."
            ]
        ),
        subject="board",
        fields=fields,
        form=form,
    )


@board.route("/new/")
def new_board():
    return redirect(
        url_for(
            ".edit_board", board_id=''.join(
                choices(ascii_lowercase + digits, k=5)
            )
        ), code=307
    )


@board.route("/delete/<string:board_id>/")
def delete_board(board_id: str):
    flash("Deleted board " + boards[board_id].name)
    del boards[board_id]
    return redirect(url_for(".list_boards"))


@board.route("/activate/<string:board_id>")
def activate_board(board_id: str):
    boards[board_id].active = True
    boards.save()
    flash("Board " + boards[board_id].name + " is now set as active.")
    return redirect(url_for(".list_boards"))


@board.route("/deactivate/<string:board_id>")
def deactivate_board(board_id: str):
    boards[board_id].active = False
    boards.save()
    flash(
        "Board " + boards[board_id].name + " is now set as inactive."
    )
    return redirect(url_for(".list_boards"))
