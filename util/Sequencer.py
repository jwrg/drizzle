from threading import Timer
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

    # A reference to a Timer object; this is initialized as
    # None, which denotes that there is no active sequence
    sequence_timer = None

    # Functions for reading/updating the local sequences json
    # file.  Returns a dict, since the top-level type is object
    def getSequences():
        with open('sequences.json', 'r') as file:
            return load(file)

    def putSequences(data):
        with open('sequences.json', 'w') as file:
            return dump(data, file, sort_keys=False)

    # Returns string of currently active sequence id,
    # otherwise returns a blank string (not None)
    def getSequenceState():
        return '' if Sequencer.sequence == None else str(Sequencer.sequence)

    # Functional means for executing a sequence
    def executeSequence(index: int, sequence):
        if index > 0:
            Platelet.zoneOff(sequence[str(index - 1)]['zone'])
        if index < len(sequence) - 1:
            Platelet.zoneOn(sequence[str(index)]['zone'])
            Sequencer.sequence_timer = Timer(60.0 * sequence[str(index)]['minutes'],\
                    Sequencer.executeSequence, [index + 1, sequence])
            Sequencer.sequence_timer.start()
        else:
            Platelet.pumpOff()
            Sequencer.sequence = None
            Sequencer.sequence_timer = None

    # Sets up and activates the sequence with specified
    # id number
    def initSequence(id):
        if Sequencer.sequence == None:
            Sequencer.sequence = int(id)
            Sequencer.executeSequence(0, Sequencer.getSequences()[str(id)]['sequence'])

    # Cancels any currently active sequence (and heavy-handedly
    # turns off all zones for good measure)
    def cancelSequence():
        if Sequencer.sequence_timer != None:
            Sequencer.sequence_timer.cancel()
            Sequencer.sequence_timer = None
        Platelet.allOff()
        Sequencer.sequence = None
