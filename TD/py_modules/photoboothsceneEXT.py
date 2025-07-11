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


class PhotoboothSceneEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self._createControlsPage()
        pass

    def _onEnterscene(self):
        self.Print('Entering Photobooth Scene')
        op.fade_control.par.Fadein.pulse()
        pass
    
    def _onExitscene(self):
        self.Print('Exiting Photobooth Scene')
        op.fade_control.par.Fadeout.pulse()
        pass
    
    def HandleButtonPress(self, current_scene):
        print(self.Me)
        current_scene = self.Me.name
        print(f"Handling button press for scene: {current_scene}")
        if current_scene == op.state_control.par.Scenename.eval():
            self.Me.par.Exitscene.pulse()
            
        pass

    def HandleLoadingComplete(self, current_scene: str) -> None:
        if current_scene == op.state_control.par.Scenename.eval():
            self.Me.par.Exitscene.pulse()
        pass
    
    def OnInit(self):
        # return False if initialization fails
        return True

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


    def _createControlsPage(self) -> None:
        page = self.GetPage('Controls')
        pars = [
            ParTemplate('EnterScene', par_type='Pulse', label='EnterScene'),
            ParTemplate('ExitScene', par_type='Pulse', label='ExitScene'),
        ]
        for par in pars:
            par.createPar(page)

        pass

