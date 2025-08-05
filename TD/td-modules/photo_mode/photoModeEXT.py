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
try:
    from photoboothsceneEXT import PhotoboothSceneEXT  #type: ignore
except ModuleNotFoundError():
    from ...py_modules.photoboothsceneEXT import PhotoboothSceneEXT #pylint: disable=relative-beyond-top-level


class PhotoModeEXT(PhotoboothSceneEXT):
    def __init__(self, myop: OP) -> None:
        PhotoboothSceneEXT.__init__(self, myop,"button_press")
        self._createCustomPars()
        pass

    def OnInit(self):
        # return False if initialization fails
        return True
    
    def _onEnterscene(self):
        op.loading_control.op("loading_bar").par.Initialize.pulse()
        if self.Me.par.Showerrormessage:
            self.Me.op("error_timer").par.start.pulse()
        super()._onEnterscene()
        pass

    def HandleZoom(self, zoom_amt):
        print("zoom", op("constant2").par.const0value)
        if self.Me.par.Buttonpressed:
            return
        current_zoom = (op("constant2").par.const0value)
        if zoom_amt == 1 and current_zoom < 2:
            op("constant2").par.const0value = current_zoom + 1
        elif zoom_amt == 0 and current_zoom > 0:
            op("constant2").par.const0value = current_zoom - 1
        print("zoom", op("constant2").par.const0value)
        pass
    
    def HandleButtonPress(self, button_name: str) -> None:
        op.camera_control.par.Capturecamerafeed.pulse()
        op.loading_control.par.Canfinish = 0
        super().HandleButtonPress(button_name)
        # Implement your button handling logic here
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

    def _createCustomPars(self) -> None:
        page = self.GetPage('PhotoSelect')
        
        pars = [
            ParTemplate('ShowErrorMessage', par_type='Toggle', label='Show Error Message'),
        ]


        for par in pars:
            par.createPar(page)

        pass
