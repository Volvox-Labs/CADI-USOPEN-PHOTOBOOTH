# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
# from vvox_tdtools.parhelper import ParTemplate
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
    from photoboothsceneEXT import PhotoboothSceneEXT  # type: ignore
except ModuleNotFoundError():
    from ...py_modules.photoboothsceneEXT import PhotoboothSceneEXT  # pylint: disable=relative-beyond-top-level

class AttractVideoSceneEXT(PhotoboothSceneEXT):
    def __init__(self, myop: OP) -> None:
        PhotoboothSceneEXT.__init__(self, myop,"video_complete")
        pass

    def OnInit(self):
        # return False if initialization fails
        return True

    def _onEnterscene(self):
        self.Me.op("intro_video").par.play = 1
        self.Me.op("intro_video").par.cuepulse.pulse()
        self.Me.par.Buttonpressed = 0
        super()._onEnterscene()
        pass

    def _onExitscene(self):
        self.Me.op("intro_video").par.play = 0
        self.Me.par.Buttonpressed = 0
        super()._onExitscene()
        pass
        
    def HandleButtonPress(self, current_scene):
        if not self.Me.par.Buttonpressed: 
            self._onExitscene()
        pass

    def HandleVideoComplete(self):
        if not self.Me.par.Buttonpressed and op.state_control.par.State.eval() == 1:
            self.Me.par.Exitscene.pulse()
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


