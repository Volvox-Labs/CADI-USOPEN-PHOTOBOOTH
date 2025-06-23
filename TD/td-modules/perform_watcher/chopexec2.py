try:
    # import td
    from td import op, root
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import op, root  #pylint: disable=ungrouped-imports

def open_main_window():
    if root.var('mode') == 'production':
        if op('/main') is None:
            return
        if not op('/main').isOpen:
            op('/main').par.winopen.pulse()
    return

def onOffToOn(channel, sampleIndex, val, prev):
    open_main_window()
    return

def whileOn(channel, sampleIndex, val, prev):
    return

def onOnToOff(channel, sampleIndex, val, prev):
    return

def whileOff(channel, sampleIndex, val, prev):
    return

def onValueChange(channel, sampleIndex, val, prev):
    return
