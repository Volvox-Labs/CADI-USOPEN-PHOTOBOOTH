try:
    # import td
    from td import op, run, monitors # type: ignore
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import op, run, monitors  #pylint: disable=ungrouped-imports


def onOffToOn(channel, sampleIndex, val, prev):
    if len(monitors) > 1:
        is_headless = op.config.fetch('data')['vars']['headless']
        if is_headless:
            return
        main_op = op('/main')
        if not main_op.isOpen:
            run("op('/main').par.winopen.pulse()", delayMilliSeconds=100)
    return

def whileOn(channel, sampleIndex, val, prev):
    return

def onOnToOff(channel, sampleIndex, val, prev):
    return

def whileOff(channel, sampleIndex, val, prev):
    return

def onValueChange(channel, sampleIndex, val, prev):
    return
