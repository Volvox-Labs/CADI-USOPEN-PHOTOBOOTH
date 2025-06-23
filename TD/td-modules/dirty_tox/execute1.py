# pylint: disable=missing-docstring

try:
    # import td
    from td import op, ui, COMP, parent
    TDJ = op.TDModules.mod.TDJSON
    TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import op, ui, COMP, parent  #pylint: disable=ungrouped-imports

def find_dirty():
    # print('find dirty')
    comp_ops = op('/').findChildren(type=COMP)
    dirty_comps = []
    linked_to = []
    # print(comp_ops)
    if len(comp_ops) == 0:
        print('no comps found')
    else :
        for comp_op in comp_ops:
            comp_link = comp_op.par.externaltox
            if comp_op.dirty:
                linked_to.append(comp_link)
                dirty_comps.append(comp_op)
    return dirty_comps

def fill_table(dirty_comps):
    dirty_table = op('table_dirty_ops')
    path_col = [comp.path for comp in dirty_comps]
    if len(path_col) == 0:
        path_col = ['']
    dirty_table.clear()
    dirty_table.appendCol(path_col)

    pass

def onFrameEnd(frame):
    if ui.performMode:
        return
    if not parent().par.Active.val:
        return
    if frame % 60 == 0:
        dirty_comps = find_dirty()
        # print('dirty_comps', dirty_comps)
        fill_table(dirty_comps)
    return
