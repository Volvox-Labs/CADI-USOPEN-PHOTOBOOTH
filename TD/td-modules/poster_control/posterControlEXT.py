# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
from vvox_tdtools.parhelper import ParTemplate
import datetime

try:
    # import td
    from td import OP, op  # type: ignore
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, op  # pylint: disable=ungrouped-imports
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF


class PosterControlEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self.Me.par.opshortcut = 'poster_control'
        self._createControlsPage()
        pass

    def OnInit(self):
        # return False if initialization fails
        return True

    def CreateTakeaway(self):
        self.Logger.debug("Creating takeaway ")
        self.Me.op("intro_timer").par.initialize.pulse()
        self.Me.op("poster_timer").par.initialize.pulse()
        self.Me.op("scale_timer").par.initialize.pulse()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sharable_{timestamp}.mp4"
        self.Me.par.Filename = filename
        # op("camera_capture").par.file = self.Me.par.Outputpath + filename
        self.Me.op("intro_timer").par.start.pulse()
        pass

    def _onRecordtakeaway(self):
        self.CreateTakeaway()

    def HandleRecordingComplete(self):
        self.Logger.debug("Recording Complete ")
        op.loading_control.par.Canfinish = 1
        op.poster_control.par.Takeawayrecording = 0
        op.loading_control.HandleLoadingCanFinish()
        self.Me.op("intro_timer").par.initialize.pulse()
    pass

    def CheckForEmptyMask(self):
        return self.Me.op("CheckForBlank/mask_alpha")["a"].eval() == 0
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
    #     self.self.Logger.debug('every second')
    #     pass

    def _createControlsPage(self) -> None:
        page = self.GetPage('Controls')
        takeaway_recording_toggle = ParTemplate(
            "TakeawayRecording", par_type="Toggle", label="TakeawayRecording")
        takeaway_recording_toggle.readOnly = True
        pars = [
            ParTemplate("CaptureMosaicPhoto", par_type="Pulse",
                        label="CaptureMosaicPhoto"),
            ParTemplate('MosaicCapturePath', par_type='Folder',
                        label='MosaicCapturePath'),
            ParTemplate('CapturePath', par_type='File', label='CapturePath'),
            ParTemplate('UseTestCapture', par_type='Toggle',
                        label='UseTestCapture'),
            ParTemplate("TestCaptureOption", par_type="Int",
                        label="TestCaptureOption"),
            ParTemplate("FileName", par_type="Str", label="FileName"),
            ParTemplate("RecordTakeaway", par_type="Pulse",
                        label="RecordTakeaway"),
            ParTemplate("TakeawayOutputPath", par_type="Str",
                        label="TakeawayOutputPath"),
            takeaway_recording_toggle,
        ]
        for par in pars:
            par.createPar(page)

        page = self.GetPage('Style')
        
        enable_style_mode_par = ParTemplate(
            "EnableStyleMode", par_type="Toggle", label="EnableStyleMode")
        
        scale_par = ParTemplate("Scale", par_type="Float", label="Scale")
        scale_par.default = 1.66
        scale_par.enableExpr = "me.par.Enablestylemode.eval()"
        
        translate_y_par = ParTemplate("TranslateY", par_type="Float", label="TranslateY")
        translate_y_par.default = -0.03
        translate_y_par.enableExpr = "me.par.Enablestylemode.eval()"
        
        profile_scale_par = ParTemplate("ProfileScale", par_type="Float", label="ProfileScale")
        profile_scale_par.default = 0.299
        profile_scale_par.enableExpr = "me.par.Enablestylemode.eval()"

        profile_transform_x_par = ParTemplate("ProfileTransformX", par_type="Float", label="ProfileTransformX")
        profile_transform_x_par.default = -0.03
        profile_transform_x_par.enableExpr = "me.par.Enablestylemode.eval()"

        profile_transform_y_par = ParTemplate("ProfileTransformY", par_type="Float", label="ProfileTransformY")
        profile_transform_y_par.default = 0.03
        profile_transform_y_par.enableExpr = "me.par.Enablestylemode.eval()"

        althea_scale_par = ParTemplate("AltheaScale", par_type="Float", label="AltheaScale")
        althea_scale_par.default = 0.14
        althea_scale_par.enableExpr = "me.par.Enablestylemode.eval()"

        althea_transform_x_par = ParTemplate("AltheaTransformX", par_type="Float", label="AltheaTransformX")
        althea_transform_x_par.default = -0.171
        althea_transform_x_par.enableExpr = "me.par.Enablestylemode.eval()"

        althea_transform_y_par = ParTemplate("AltheaTransformY", par_type="Float", label="AltheaTransformY")
        althea_transform_y_par.default = -0.01
        althea_transform_y_par.enableExpr = "me.par.Enablestylemode.eval()"

        pars = [enable_style_mode_par,scale_par,translate_y_par, profile_scale_par, profile_transform_x_par, profile_transform_y_par, althea_scale_par, althea_transform_x_par, althea_transform_y_par]
        for par in pars:
            par.createPar(page)

        pass
