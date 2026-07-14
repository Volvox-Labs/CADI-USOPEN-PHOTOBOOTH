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


class UploadControlEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self._createControlsPage()
        self.Me.par.opshortcut = 'upload_control'
        #TODO this should just be set via state control
        pass

    def OnInit(self):
        # return False if initialization fails
        return True

    def HandleFailedUpload(self):
        self.Logger.debug("Handling Failed Upload")
        # op.photo_capture.par.Showerrormessage = 1

        pass

    def HandleUploadResult(self, result):
        if not result:
            self.Logger.debug("HandleUploadResult called with no result")
            return
        status = result.get("status")
        if status == "video_upload_success":
            qr_code_path = result.get("qr_code_path")
            if qr_code_path:
                op.qrcode_scene.op("qrcode_file").par.file = qr_code_path
                self.Logger.debug(f"QR code path: {qr_code_path}")
                op.upload_control.par.Status = "complete"
            else:
                self.Logger.debug("No QR code path found in upload result")
        elif status == "video_upload_error":
            op.upload_control.par.Status = "error"
            self.Logger.debug(f"Video upload failed: {result.get('message')}")
        else:
            self.Logger.debug(f"Received unknown upload result: {result}")

    def HandleUploadException(self, args):
        self.Logger.error(f"Upload thread raised an exception: {args}")
        op.upload_control.par.Status = "error"
        self.HandleFailedUpload()

    def GetTakeawayFileName(self):
        colors = ["blue","red","white","yellow"]
        selected_poster_index = int(op.photo_select.par.Selectedphoto.eval()) - 1
        return op.poster_control.par.Takeawayoutputpath + colors[selected_poster_index] + "_" + op.poster_control.par.Filename

    def _onUploadvideo(self):
        movie = self.Me.par.Filepath.eval()
        self.Logger.debug(f"uploading movie: {movie}")
        op.upload_control.par.Status = "processing"
        self.Me.op("threadManagerClient").par.Runinthread.pulse()
        self.Logger.debug("started upload thread")
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
    #     self.self.Logger.debug('every second')
    #     pass


    def _createControlsPage(self) -> None:
        page = self.GetPage('Controls')
        status_par = ParTemplate('Status', par_type='Str', label='Status')
        status_par.readOnly = True
        status_par.default = "inactive"

        pars = [
            ParTemplate('UploadVideo', par_type='Pulse', label='UploadVideo'),
            status_par,
            ParTemplate("FilePath",par_type="File",label="FilePath")

        ]
        for par in pars:
            par.createPar(page)

        pass

