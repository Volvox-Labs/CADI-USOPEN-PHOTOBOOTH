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


class StateControlEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self._createControlsPage()
        self.Me.par.opshortcut = "state_control"
        self.HomeScene = op.state_control.op("state_table").findCell("attract_scene").row
        self.PhotoCaptureScene = op.state_control.op("state_table").findCell("photo_capture_scene").row
        self.VideoAttractScene = op.state_control.op("state_table").findCell("attract_video_scene").row
        pass

    def OnInit(self):
        # return False if initialization fails
        return True
    
    def HandleSceneTimeout(self):
        print("sene timeout ")
        print("Setting next state to video attract")
        self.Me.par.Nextstate = self.VideoAttractScene
        op.state_control.par.Sceneop.eval().par.Exitscene.pulse()
        pass
    
    def HandleExperienceComplete(self):
        states = op.state_control.op("state_table")
        op.upload_control.par.Status = "inactive"
        op.qrcode_scene.par.Showqrcode = 0
        op.photo_capture.par.Showerrormessage = 0
        for index, row in enumerate(states.rows()):
            if index > 0:
                scene = (states[index,"container_name"])
                op(f"/project1/output/{scene}").par.Buttonpressed = False
    
    def HandleFadeOutComplete(self):
        # next_state = self.Me.op("state_table")[self.Me.par.State, "goto"].val
        next_state = self.Me.par.Nextstate.eval()
        next_fade_variation = self.Me.op("state_table")[self.Me.par.State, "fade_variation"].val
        op.fade_control.par.Fadevariation = next_fade_variation
        self.Me.par.State = next_state
        self.Me.par.Sceneop.eval().par.Enterscene.pulse()
        op.fade_control.par.Fadeincomplete = 0
        if self.Me.par.State == self.HomeScene:
            self.HandleExperienceComplete()
        pass
    # Below is an example of a parameter callback. Simply create a method that starts with "_on" and then the name of the parameter.

    def _onResetphotobooth(self):
        self.Me.par.State = 2
        self.Me.par.Sceneop.eval().par.Enterscene.pulse()
        self.HandleExperienceComplete()
        op.fade_control.par.Fadevariation = self.Me.op("state_table")[1, "fade_variation"].val

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
            ParTemplate('State', par_type='Int', label='State'),
            ParTemplate('NextState', par_type='Int', label='NextState'),
            ParTemplate('ResetPhotoBooth', par_type='Pulse', label='ResetPhotoBooth'),
            ParTemplate('CaptureMode', par_type='Toggle', label='CaptureMode'),
            ParTemplate('PhotoBoothActive', par_type='Toggle', label='PhotoBoothActive'),
            ParTemplate("DevMode",par_type="Toggle",label="DevMode")

        ]

        scene_name = ParTemplate('SceneName', par_type='Str', label='Scene Name')
        scene_name.expr = "op('./state_table')[me.par.State.eval(), 'container_name'].val"
        scene_name.readOnly = True
        pars.append(scene_name)
        scene_op = ParTemplate('SceneOp', par_type='OP', label='Scene Op')
        scene_op.expr = "op('/project1/output/' +  me.par.Scenename.eval())" 
        scene_op.readOnly = True
        pars.append(scene_op)
        # scene_name = self.Me.op('state_table')[self.Me.par.State.eval(), 'container_name'].val
        
        for par in pars:
            par.createPar(page)

        pass

