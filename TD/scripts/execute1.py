try:
    # import td
    from td import op, monitors, root # type: ignore
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import op, monitors, root  #pylint: disable=ungrouped-imports

def find_main_monitor():
    main_mon_index = 0
    for idx, monitor in enumerate(monitors):
        if monitor.isPrimary:
            main_mon_index = idx
    return main_mon_index

def onStart():
    is_production = root.var('mode') == 'production'
    is_headless = op.config.fetch('data')['vars']['headless']
    if is_production and not is_headless:
        if op('main') is None:
            return
    status_op = op('/window_status_view')
    status_op.par.monitor.val = 0
    if len(monitors) > 1:
        if is_headless:
            status_op.par.monitor.val = find_main_monitor()
    
    if is_production:
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

    