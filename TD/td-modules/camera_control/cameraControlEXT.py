# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
from vvox_tdtools.parhelper import ParTemplate
import datetime
try:
    # import td
    from td import OP # type: ignore
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP  #pylint: disable=ungrouped-imports 
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF


class CameraControlEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self.Me.par.opshortcut = 'camera_control'
        self._createControlsPage()
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

    def _onCapturecamerafeed(self, par):
        # This method should handle the camera feed capture logic
        print('Capturing camera feed...')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/capture_{timestamp}.png"
        op("camera_capture").par.file = self.Me.par.Outputpath + filename
        print(f"Saving camera feed to {filename}")
        op("camera_capture").par.addframe.pulse()
        # Implement the logic to capture the camera feed here
        pass

    def _createControlsPage(self) -> None:
        page = self.GetPage('Controls')
        pars = [
            ParTemplate('CaptureCameraFeed', par_type='Pulse', label='CaptureCameraFeed'),
            ParTemplate("OutputPath", par_type='Folder', label='OutputPath'),
        ]
        for par in pars:
            par.createPar(page)

        pass

