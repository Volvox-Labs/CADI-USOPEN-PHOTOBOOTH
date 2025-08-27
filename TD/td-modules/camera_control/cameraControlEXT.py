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

        self.info_chop = self.Me.op("info_b1") if int(root.var("blackmagic_camera_index")) == 0 else self.Me.op("info_b2")
        pass

    def OnInit(self):
        # return False if initialization fails
        return True

 
    def HandleHeartbeatCycle(self):
        
        current_frame = self.info_chop["frame_timestamp"].eval()
        if current_frame == float(op.camera_control.op("heartbeat_frame").text):
            self.Me.par.Cameraconnected = False
        else:
            self.Me.par.Cameraconnected = True
            self.Me.op("heartbeat_frame").text = current_frame

    def HeartbeatStart(self):
        self.Me.op("heartbeat_frame").text = self.info_chop["frame_timestamp"].eval()
        pass
    def _onCapturecamerafeed(self, par):
        # This method should handle the camera feed capture logic
        self.Logger.debug('Capturing camera feed...')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.png"
        op("camera_capture").par.file = self.Me.par.Outputpath + filename
        self.Logger.debug(f"Saving camera feed to {filename}")
        op("camera_capture").par.addframe.pulse()
        # Implement the logic to capture the camera feed here
        pass

    def _createControlsPage(self) -> None:
        page = self.GetPage('Controls')

        camera_connected = ParTemplate("CameraConnected", par_type='Toggle', label='CameraConnected')
        camera_connected.readOnly = True
        pars = [
            ParTemplate('CaptureCameraFeed', par_type='Pulse', label='CaptureCameraFeed'),
            ParTemplate("OutputPath", par_type='Folder', label='OutputPath'),
            ParTemplate("UseTestCapture", par_type='Toggle', label='UseTestCapture'),
            camera_connected
        ]
        for par in pars:
            par.createPar(page)

        pass

