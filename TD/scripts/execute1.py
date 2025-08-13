try:
    # import td
    from td import op, monitors, root # type: ignore
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import op, monitors, root  #pylint: disable=ungrouped-imports

def onStart():

    op('main').par.winopen.pulse()

    return

def onCreate():
    return

def onExit():
    return

def onFrameStart(frame):
    return

def onFrameEnd(frame):
    return

def onPlayStateChange(state):
    return

def onDeviceChange():
    return

def onProjectPreSave():
    return

def onProjectPostSave():
    return

    