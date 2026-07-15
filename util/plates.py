from flask import current_app

platestate = [0 for zero in range(0, 7)]


def relaySTATE(board_index):
    return platestate[board_index]


def relayON(board_index, relay_index):
    platestate[board_index] = platestate[board_index] | 1 << relay_index - 1
    current_app.logger.debug(
        ' '.join(
            [
                "Board with index",
                str(board_index),
                "relay with index",
                str(relay_index),
                "is now turned on"
            ]
        )
    )
    current_app.logger.debug(
        ' '.join(
            [
                "New state for board with index",
                str(board_index),
                "is",
                str(platestate[board_index]),
                "[ {0:0>7b} ]".format(platestate[board_index]),
            ]
        )
    )
    return 0


def relayOFF(board_index, relay_index):
    platestate[board_index] = platestate[board_index] & ~(1 << relay_index - 1)
    current_app.logger.debug(
        ' '.join(
            [
                "Board with index",
                str(board_index),
                "relay with index",
                str(relay_index),
                "is now turned off"
            ]
        )
    )
    current_app.logger.debug(
        ' '.join(
            [
                "New state for board with index",
                str(board_index),
                "is",
                str(platestate[board_index]),
                "[ {0:0>7b} ]".format(platestate[board_index]),
            ]
        )
    )
    return 0
