# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
from vvox_tdtools.parhelper import ParTemplate
try:
    # import td
    from td import OP # type: ignore
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP  #pylint: disable=ungrouped-imports 
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF
try:
    from photoboothsceneEXT import PhotoboothSceneEXT  #type: ignore
except ModuleNotFoundError():
    from ...py_modules.photoboothsceneEXT import PhotoboothSceneEXT #pylint: disable=relative-beyond-top-level


class LoadingEXT(PhotoboothSceneEXT):
    def __init__(self, myop: OP) -> None:
        PhotoboothSceneEXT.__init__(self, myop,"loading")
        self._createLoadingControls()
        pass

    def OnInit(self):
        # return False if initialization fails
        return True
    
    def HandleLoadingCanFinish(self):
        self.Me.op("loading_bar").op("timer2").goTo(segment=2)
        pass

    # Below is an example of a parameter callback. Simply create a method that starts with "_on" and then the name of the parameter.

    # def _onExampletoggle(self, par):
    #     self.Logger.debug(f"_onExampleToggle - val: {par.eval()}")
    #     pass

    # Below is an example of creating an event loop by overriding the OnFrameStart method.

    # def OnFrameStart(self, frame: int):
    #     if frame % 60 == 0:
    #         self.OnEventLoop1()
    #     return 

    # def OnEventLoop1(self):
    #     self.Print('every second')
    #     pass

    def _createLoadingControls(self) -> None:
        page = self.GetPage('LoadingControls')
        pars = [
            ParTemplate('CanFinish', par_type='Toggle', label='CanFinish'),

        ]
        for par in pars:
            par.createPar(page)

        pass