# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
from vvox_tdtools.parhelper import ParTemplate
import datetime
try:
    # import td
    from td import OP  # type: ignore
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP  # pylint: disable=ungrouped-imports
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF

try:
    from photoboothsceneEXT import PhotoboothSceneEXT  # type: ignore
except ModuleNotFoundError():
    from ...py_modules.photoboothsceneEXT import PhotoboothSceneEXT  # pylint: disable=relative-beyond-top-level


class PhotoSelectEXT(PhotoboothSceneEXT):
    def __init__(self, myop: OP) -> None:
        PhotoboothSceneEXT.__init__(self, myop,"button_press")
        self.Me.par.opshortcut = 'photo_select'
        self._createPhotoSelectControls()
        self.CurrentButton = 0
        for i in range(1,5):
            self.Me.op(f"photo_button{i}").par.Clicked = 0
        self.Me.op("photo_button3").par.Clicked = 1
        self.Me.par.Selectedphoto = 3
        photo_capture_row = op.state_control.op("state_table").findCell("photo_capture_scene").row
        self.retake_photo_state_id = op.state_control.op("state_table")[photo_capture_row, "state id"].val
        print(self.retake_photo_state_id)
        
        pass

    def OnInit(self):
        # return False if initialization fails
        return True
    
    def SendPoster(self):
        colors = ["blue","red","white","yellow"]
        selected_poster_index = int(self.Me.par.Selectedphoto.eval()) - 1
        selected_poster_name = f"poster{colors[selected_poster_index]}"
        print(selected_poster_name)
        op.poster_control.op("selectposter").par.top = selected_poster_name
        op.upload_control.par.Uploadvideo.pulse()
        pass
    
    
    
    def HandleButtonPress(self, current_scene):
        # DO SOMETHING HERE WITH THE IMAGE
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/mosaic_{timestamp}.png"
        mosaic_photo_index = self.Me.op(f"photo_button{self.Me.par.Selectedphoto.eval()}").par.Index.eval()
        op.poster_control.par.Coloroption = (mosaic_photo_index)
        op.poster_control.op("mosaic_capture").par.file = op.poster_control.par.Mosaiccapturepath + filename
        op.poster_control.par.Capturemosaicphoto.pulse()
        self.SendPoster()
        super().HandleButtonPress(current_scene)
        pass

    def HandleRetakePhoto(self):
        op.state_control.par.Nextstate = self.retake_photo_state_id
        super().HandleButtonPress(self.Me.name)

    def HandleImageSelected(self, channel, button_state):
        print(
            f"HandleImageSelected - channel: {channel.name}, button_state: {button_state}")
        image_index = channel.name.replace('button', '')
        self.Me.op(f"photo_button{self.Me.par.Selectedphoto}").par.Clicked = 0
        self.Me.op(f"photo_button{image_index}").par.Clicked = 1
        
        # if self.Me.par.Photoselected:
            # self.Me.op(f"photo_button{image_index}").par.
        self.Me.par.Selectedphoto = int(image_index)
        
        # self.Me.par.Photoselected = button_state
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

    def _createPhotoSelectControls(self) -> None:
        page = self.GetPage('PhotoSelectControls')
        pars = [
            ParTemplate('SelectedPhoto', par_type='Int',
                        label='SelectedPhoto'),

        ]

        photo_selected = ParTemplate(
            'PhotoSelected', par_type='Toggle', label='PhotoSelected')
        photo_selected.readOnly = True
        pars.append(photo_selected)

        for par in pars:
            par.createPar(page)

        pass
