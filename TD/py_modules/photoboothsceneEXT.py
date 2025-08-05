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
    def __init__(self, myop: OP, scene_exit_type: str) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self._createControlsPage()
        self.scene_exit_type = scene_exit_type
        pass

    def _onEnterscene(self):
        self.Print('Entering Photobooth Scene')
        op.fade_control.par.Fadein.pulse()
        self.Me.par.Buttonpressed = 0
        op.state_control.par.Nextstate = op.state_control.op("state_table")[op.state_control.Me.par.State, "goto"].val
        op.state_control.op("inactivity_timeout").par.cuepulse.pulse()
        pass
    
    def _onExitscene(self):
        self.Print('Exiting Photobooth Scene')
        op.fade_control.par.Fadeout.pulse()
        pass
    
    # def _onButtonpress(self):
    #     print(self.Me.name)
    #     self.Me.par.Buttonpressed = 1
    
    def HandleButtonPress(self, current_scene):
        print(f"Handling button press for scene: {current_scene}")
        current_scene = self.Me.name
        op.state_control.op("idle_timeout").par.initialize.pulse()
        self.Me.par.Buttonpress.pulse()
        self.Me.par.Buttonpressed = 1
        
        if current_scene == op.state_control.par.Scenename.eval() and op.fade_control.par.Fadeincomplete.eval():
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
            ParTemplate("ButtonPress", par_type="Pulse", label="ButtonPress"),
            ParTemplate("ButtonPressed", par_type="Toggle", label="ButtonPressed"),
            
        ]
        for par in pars:
            par.createPar(page)

        pass

