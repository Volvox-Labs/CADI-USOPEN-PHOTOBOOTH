# pylint: disable=missing-docstring
# import pathlib
from vvox_tdtools.base import BaseEXT
try:
    # import td
    from td import OP, op, parent
    TDJ = op.TDModules.mod.TDJSON
    TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, ParMode, parent  #pylint: disable=ungrouped-imports
    from tdconfig import TDJSON as TDJ
    from tdconfig import TDFunctions as TDF


class SceneEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop)
        self.Me.par.opshortcut.mode = ParMode.CONSTANT
        self.Me.par.opshortcut.val = ''
        self._addScenePars()
        self.IsVideo = False
        pass

    def OnStart(self):
        self.print('OnStart')
        pass

    def OnCreate(self):
        self.print('OnCreate')
        pass

    def Cuein(self):
        self.print('Cue In')
        pass

    def Cueout(self):
        self.print('Cue Out')
        pass

    def Visible(self):
        self.print('OnVisible')
        pass

    def Selected(self):
        self.print('OnSelected')
        pass

    def _addScenePars(self):
        scene_pars_op = self.Me.op('scene_pars')
        if scene_pars_op is None:
            scene_pars_op = parent.scene.op('blank_scene/scene_pars')
        # print('scene_pars', scene_pars_op)
        default_pars = TDJ.datToJSON(scene_pars_op)
        TDJ.addParametersFromJSONDict(self.Me,
                                      default_pars,
                                      replace=True,
                                      setValues=False)
        pass

    def CopyStateParsToDat(self, dat, page: str = 'State'):
        state_page = TDF.getCustomPage(self.Me, page)
        par_dict = TDJ.pageToJSONDict(state_page, extraAttrs=['mode', 'expr'])
        TDJ.jsonToDat(par_dict, dat)
        pass

    def Print(self, *args):
        str_args = [str(x) for x in args]
        message = ' '.join(str_args)
        return self.print(message)
