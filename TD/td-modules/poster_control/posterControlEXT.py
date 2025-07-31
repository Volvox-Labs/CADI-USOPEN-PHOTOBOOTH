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
        print("Creating takeaway ")
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
        print("Recording Complete ")
        op.loading_control.par.Canfinish = 1
        op.poster_control.par.Takeawayrecording = 0
        self.Me.op("intro_timer").par.initialize.pulse()
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

        pass
