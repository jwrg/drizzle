from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from flask import current_app

from util.persist import PersistentMapping
from util.singleton import singleton
from util.relay import Relay


@dataclass
class Connection:
    """
    Dataclass for coupling a board index (address on a board) with a
    reference to a Relay object
    """
    index: int
    relay: Relay


class Board:
    """
    Class that constrains where relays can be located, and keeps track of
    which indices on a board have relays associated with them
    """

    logger = current_app.logger

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        index: int,
        type: str,
        active: bool = True,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.index = index
        self.type = type
        self.active = active
        self.addresses = [
            Connection(x, None) for x in range(1, 8)
        ]
        Board.logger.debug(" ".join(["Board", str(self.name), "initialized"]))

    def __str__(self):
        return self.id

    def __getitem__(self, index):
        return self.addresses[index - 1].relay

    def __len__(self):
        return len(self.get_valid_addresses()) - len(self.get_open_addresses())

    def __setitem__(self, index: int, relay: Relay):
        if index not in self.get_open_addresses():
            Board.logger.debug(
                " ".join(
                    [
                        "Board",
                        str(self.name),
                        "did not register relay",
                        relay.name,
                        "at address",
                        str(index),
                        "is already assigned."
                    ]
                )
            )
            raise ValueError
        self.addresses[index - 1].relay = relay
        Board.logger.debug(
            " ".join(
                [
                    "Board",
                    str(self.name),
                    "successfully registered",
                    relay.name,
                    "at address",
                    str(index) + "."
                ]
            )
        )

    def __delitem__(self, index: int) -> None:
        if index in self.get_open_addresses():
            Board.logger.debug(
                " ".join(
                    [
                        "Board",
                        str(self.name),
                        "did not un-register a relay",
                        "at address",
                        str(index) + ";",
                        "the address is not assigned."
                    ]
                )
            )
            raise ValueError
        self.addresses[index - 1].relay = None
        Board.logger.debug(
            " ".join(
                [
                    "Board",
                    str(self.name),
                    "un-registered",
                    "address",
                    str(index) + "."
                ]
            )
        )

    def get_open_addresses(self) -> list[int]:
        return [
            conn.index for conn
            in self.addresses
            if conn.relay is None
        ]

    def get_valid_addresses(self) -> list[int]:
        return [conn.index for conn in self.addresses]


@singleton
class Holder(PersistentMapping):
    """
    Class for keeping track of Board objects
    """

    default_filename = "boards"
    logger = current_app.logger

    def __init__(self, filename: str = default_filename):
        super().__init__(filename)

    def __delitem__(self, key):
        from util.relay import Baton
        relays = Baton()
        for conn in self.collection[key].addresses:
            if conn.relay is not None:
                del relays[conn.relay.id]
                conn.relay = None
            del conn
        Holder.logger.debug(
            " ".join(
                [
                    "Board",
                    self.collection[key].name,
                    "with id",
                    self.collection[key].id,
                    "deleted.",
                ]
            )
        )
        super().__delitem__(key)

    def register(self, board_index: int, relay_index: int, relay: Relay):
        board = next(
            (
                b for b in self.collection.values()
                if b.index == board_index
            ), None
        )
        if board is not None:
            board[relay_index] = relay

    def to_obj(self, collection: dict[str, dict[str, str]]) -> dict[str, Board]:
        return {
            id: Board(
                **{
                    "id": id,
                    "name": board["name"],
                    "description": board["description"],
                    "index": board["index"],
                    "active": board["active"],
                    "type": board["type"],
                }
            )
            for id, board in collection.items()
        }

    def to_json(self, collection: dict[str, Board]) -> dict[str, dict[str, str]]:
        return {
            board.id: {
                "name": board.name,
                "description": board.description,
                "index": board.index,
                "active": board.active,
                "type": board.type,
                "modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            }
            for board in collection.values()
        }
