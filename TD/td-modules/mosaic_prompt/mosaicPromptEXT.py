# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
# from vvox_tdtools.parhelper import ParTemplate
import datetime
try:
    # import td
    from td import OP,op # type: ignore
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP,op  #pylint: disable=ungrouped-imports 
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF
try:
    from photoboothsceneEXT import PhotoboothSceneEXT  #type: ignore
except ModuleNotFoundError():
    from ...py_modules.photoboothsceneEXT import PhotoboothSceneEXT #pylint: disable=relative-beyond-top-level



class MosaicPromptEXT(PhotoboothSceneEXT):
    def __init__(self, myop: OP) -> None:
        PhotoboothSceneEXT.__init__(self, myop,"button_press")
        pass

    def OnInit(self):
        # return False if initialization fails
        return True
    
    
    def HandleMosaicPromptAnswer(self, val):
        print(f"User answered mosaic prompt with value: {val}")
        if not self.Me.par.Buttonpressed:
            if val == 1:
                print("User answered yes to mosaic prompt")
                mosaic_photo_index = op.photo_select.op(f"photo_button{op.photo_select.par.Selectedphoto.eval()}").par.Index.eval()
                op.poster_control.par.Coloroption = (mosaic_photo_index)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/mosaic_{timestamp}.png"
                op.poster_control.op("mosaic_capture").par.file = op.poster_control.par.Mosaiccapturepath + filename
                op.poster_control.op("mosaic_capture").par.addframe.pulse()
            super().HandleButtonPress(self.Me.name)
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


