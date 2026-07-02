platestate = 0


def relaySTATE(arg):
    global platestate
    return platestate


def relayON(arg, arg2):
    global platestate
    platestate = platestate | 1 << arg2 - 1
    print("__!! ON !!__".join(["BOARD", str(arg), "RELAY", str(arg2), "ON--ON--ON"]))
    print("--!STATE!--".join((["NEWSTATE:", str(platestate)])))
    return 0


def relayOFF(arg, arg2):
    global platestate
    platestate = platestate & ~(1 << arg2 - 1)
    print("__! OFF !__".join(["BOARD", str(arg), "RELAY", str(arg2), "OFF--OFF--OFF"]))
    print("--!STATE!--".join((["NEWSTATE:", str(platestate)])))
    return 0
