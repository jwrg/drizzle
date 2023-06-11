"""
Helper class for recursively sequencing relays on and off
"""
from datetime import timedelta
from threading import Lock

from flask import current_app

from util.jsonny import Jsonny
from util.platelet import Platelet


class Sequencer:
    """
    Static class that executes, cancels sequences, and handles JSON I/O to read and
    write sequence data
    """

    sequence = None
    lock = Lock()

    logger = current_app.logger

    @staticmethod
    def init_sequence(sequence_id):
        """
        Initializes and activates the sequence with specified id number
        """
        if Sequencer.sequence is None:
            Sequencer.lock.acquire()
            Sequencer.logger.info(" ".join(["Sequence", str(sequence_id), "starting."]))
            Sequencer.sequence = int(sequence_id)
            Sequencer.execute_sequence(
                0, Jsonny.get("sequences")[str(sequence_id)]["sequence"]
            )
        else:
            Sequencer.logger.debug(
                " ".join(
                    [
                        "Sequence",
                        str(sequence_id),
                        "NOT started. Sequence",
                        str(Sequencer.sequence),
                        "currently running.",
                    ]
                )
            )

    @staticmethod
    def get_sequence_state():
        """
        Returns the currently active sequence id, otherwise returns a blank
        string (sc., it does not return None)
        """
        Sequencer.logger.debug(
            " ".join(["Returned get_sequence_state() with", str(Sequencer.sequence)])
        )
        return "" if Sequencer.sequence is None else str(Sequencer.sequence)

    @staticmethod
    def execute_sequence(index: int, sequence):
        """
        Recursively executes a sequence
        NB. Don't call this, call its wrapper instead, init_sequence() above
        """
        if index > 0:
            Platelet.zones[sequence[str(index - 1)]["zone"] - 1].off()
        if index < len(sequence) - 1:
            Platelet.pump_zone.on(timedelta(minutes=sequence[str(index)]["minutes"]))
            Platelet.zones[sequence[str(index)]["zone"] - 1].on(
                timedelta(minutes=sequence[str(index)]["minutes"]),
                Sequencer.execute_sequence,
                [index + 1, sequence],
            )
        else:
            Sequencer.logger.info(
                " ".join(["Sequence", str(Sequencer.sequence), "completed."])
            )
            Sequencer.sequence = None
            Sequencer.lock.release()

    @staticmethod
    def cancel_sequence():
        """
        Cancels any currently active sequence (and heavy-handedly turns off
        all zones for good measure)
        """
        Platelet.all_off()
        Sequencer.logger.debug(
            " ".join(["Sequence", str(Sequencer.sequence), "cancelled."])
        )
        Sequencer.sequence = None
        Sequencer.lock.release()
