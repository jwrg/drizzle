"""
Helper class for recursively sequencing relays on and off
"""
from flask import current_app

from util.jsonny import Jsonny
from util.platelet import Platelet


# Class for running and handling sequences
class Sequencer:
    """
    Static class that executes, cancels sequences, and handles JSON I/O to read and
    write sequence data
    """

    # An integer for holding the id of the currently running
    # sequence.  None denotes no sequence is currently active
    # NB this obviously implies that only one sequence may
    # be active at a time
    sequence = None
    # Persist the logger object
    logger = current_app.logger

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
        Recursive method for executing a sequence
        """
        if index > 0:
            Platelet.zones[sequence[str(index - 1)]["zone"] - 1].off()
        if index < len(sequence) - 1:
            Platelet.pump_zone.on(sequence[str(index)]["minutes"])
            Platelet.zones[sequence[str(index)]["zone"] - 1].on(
                sequence[str(index)]["minutes"],
                Sequencer.execute_sequence,
                [index + 1, sequence],
            )
        else:
            Sequencer.logger.info(
                " ".join(["Sequence", str(Sequencer.sequence), "completed."])
            )
            Sequencer.sequence = None

    @staticmethod
    def init_sequence(sequence_id):
        """
        Initializes and activates the sequence with specified id number
        """
        if Sequencer.sequence is None:
            Sequencer.logger.info(" ".join(["Sequence", str(sequence_id), "started."]))
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
