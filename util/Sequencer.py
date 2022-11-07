from json import dump, load
from util.Platelet import Platelet

from flask import current_app

# Class for running and handling sequences
class Sequencer:
    # An integer for holding the id of the currently running
    # sequence.  None denotes no sequence is currently active
    # NB this obviously implies that only one sequence may
    # be active at a time
    sequence = None
    # Persist the logger object
    logger = current_app.logger

    # Functions for reading/updating the local sequences json
    # file.  Returns a dict, since the top-level type is object
    def getSequences():
        with open("sequences.json", "r") as file:
            return load(file)

    def putSequences(data):
        with open("sequences.json", "w") as file:
            return dump(data, file, sort_keys=False)

    # Returns string of currently active sequence id,
    # otherwise returns a blank string (not None)
    def getSequenceState():
        Sequencer.logger.debug(
            " ".join(["Returned getSequenceState() with", str(Sequencer.sequence)])
        )
        return "" if Sequencer.sequence == None else str(Sequencer.sequence)

    # Functional means for executing a sequence
    def executeSequence(index: int, sequence):
        if index > 0:
            Platelet.zones[sequence[str(index - 1)]["zone"] - 1].off()
        if index < len(sequence) - 1:
            Platelet.pump_zone.on(sequence[str(index)]["minutes"])
            Platelet.zones[sequence[str(index)]["zone"] - 1].on(
                sequence[str(index)]["minutes"],
                Sequencer.executeSequence,
                [index + 1, sequence],
            )
        else:
            Sequencer.logger.info(
                " ".join(["Sequence", str(Sequencer.sequence), "completed."])
            )
            Sequencer.sequence = None

    # Sets up and activates the sequence with specified
    # id number
    def initSequence(id):
        if Sequencer.sequence == None:
            Sequencer.logger.info(" ".join(["Sequence", str(id), "started."]))
            Sequencer.sequence = int(id)
            Sequencer.executeSequence(0, Sequencer.getSequences()[str(id)]["sequence"])
        else:
            Sequencer.logger.debug(
                " ".join(
                    [
                        "Sequence",
                        str(id),
                        "NOT started. Sequence",
                        str(Sequencer.sequence),
                        "currently running.",
                    ]
                )
            )

    # Cancels any currently active sequence (and heavy-handedly
    # turns off all zones for good measure)
    def cancelSequence():
        Platelet.allOff()
        Sequencer.logger.debug(
            " ".join(["Sequence", str(Sequencer.sequence), "cancelled."])
        )
        Sequencer.sequence = None
