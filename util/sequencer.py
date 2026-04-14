"""
Helper class for recursively sequencing relays on and off
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from flask import current_app

from util.persist import PersistentMapping
from util.singleton import singleton
from util.relay import Relay, Baton

relays = Baton()


@dataclass
class Sequor:
    """
    Class to hold the individual entries in a sequence
    """
    relay: Relay
    minutes: int


class Sequitur:
    """
    Class that contains and executes a sequence of relays
    """

    def __init__(
        self, id: str, name: str, description: str, sequence: list[Sequor]
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.sequence = sequence
        self.running = False
        self.current = None

    def start(self):

        def secutus(pos):
            if pos == len(self.sequence):
                self.stop()
                return
            else:
                self.running = True
                if self.current is not None:
                    self.current.off()
                self.current = self.sequence[pos].relay
                self.current.on(
                    timedelta(minutes=self.sequence[pos].minutes),
                    secutus, [pos + 1],
                )
        secutus(0)

    def stop(self):
        if self.current is not None:
            self.current.off()
        self.running = False
        self.current = None


@singleton
class Sequencer(PersistentMapping):
    """
    Class for keeping track of sequence (Sequitur) objects
    """

    default_filename = "sequences"
    logger = current_app.logger

    def __init__(self, filename: str = default_filename) -> None:
        super().__init__(filename)

    def to_obj(self, collection: dict[str, dict]) -> dict[str, Sequitur]:
        return {
            id: Sequitur(
                id,
                sequitur["name"],
                sequitur["description"],
                [
                    Sequor(relays[
                        sequor["relay"]], sequor["minutes"])
                    for sequor in sequitur["sequence"]
                ]
            )
            for id, sequitur in collection.items()
        }

    def to_json(self, collection: dict[str, Sequitur]):
        return {
            id: {
                "description": sequitur.description,
                "name": sequitur.name,
                "modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
                "sequence": [
                    {
                        "relay": sequor.relay.id,
                        "minutes": sequor.minutes,
                    }
                    for sequor in sequitur.sequence
                ]
            }
            for id, sequitur in collection.items()
        }
