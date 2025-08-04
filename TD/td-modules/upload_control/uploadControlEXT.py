# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
import json
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
        
        self.ws_client = ""
        if self.Me.op("clients").numRows == 2:
            self.ws_client = self.Me.op("clients")[1,0].val
            op.upload_control.op("webserver1").webSocketSendText(self.ws_client,json.dumps({"message": "connected"}))
        
        pass

    def OnInit(self):
        # return False if initialization fails
        return True

    def HandleNewClient(self,client):
        self.ws_client = client
        self.Me.op("clients").appendRow([client])
        pass
    
    def HandleReceiveText(self, client, text):
        print("Received text from clien t: ", text)
        if text and text !="null":
            response = json.loads(text)
            if "qr_code_path" not in response:
                return
            qr_code_path = response["qr_code_path"]
            if qr_code_path:
                op.qrcode_scene.op("qrcode_file").par.file = qr_code_path
                print(f"QR code path for {client}: {qr_code_path}")
                op.upload_control.par.Status = "complete"
                if op.state_control.par.Scenename.eval() == "qrcode_scene":
                    op.qrcode_scene.par.Showqrcode = 1
            else:
                print(f"No QR code path found in response from {client}")
        
    def HandleDisconnect(self, client):
        print("Client disconnected: ", client)
        self.Me.op("clients").deleteRow(self.Me.op("clients").findCell(client).row)
        if self.ws_client == client:
            self.ws_client = ""
        pass
    
    def GetTakeawayFileName(self):
        colors = ["blue","red","white","yellow"]
        selected_poster_index = int(op.photo_select.par.Selectedphoto.eval()) - 1
        return op.poster_control.par.Takeawayoutputpath + colors[selected_poster_index] + "_" + op.poster_control.par.Filename

    def _onUploadvideo(self):
        movie = self.GetTakeawayFileName()
        print("uploading movie: ", movie)
        msg = {"file_name": movie}
        op.upload_control.op("webserver1").webSocketSendText(self.ws_client,json.dumps(msg))
        op.upload_control.par.Status = "processing"
        print("sent upload ")
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
        status_par = ParTemplate('Status', par_type='Str', label='Status')
        status_par.readOnly = True
        status_par.default = "inactive"
        pars = [
            ParTemplate('UploadVideo', par_type='Pulse', label='UploadVideo'),
            status_par

        ]
        for par in pars:
            par.createPar(page)

        pass

