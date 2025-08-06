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


class FadeControlEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self._createControlsPage()
        self.Me.par.opshortcut = "fade_control"
        pass

    def OnInit(self):
        # return False if initialization fails
        return True

    def HandleFadeInComplete(self):
        current_scene = op.state_control.par.Sceneop.eval()
        if current_scene.par.Buttonpressed:
            current_scene.HandleButtonPress(current_scene.name)
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
        pars = [
            ParTemplate('Init', par_type='Pulse', label='Init'),
            ParTemplate('FadeIn', par_type='Pulse', label='FadeIn'),
            ParTemplate('FadeOut', par_type='Pulse', label='FadeOut'),
            ParTemplate("FadeInComplete",par_type="Toggle",label="FadeInComplete"),
            ParTemplate("FadeVariation",par_type="Int",label="FadeVariation"),
            ParTemplate("EnableTestMode",par_type="Toggle",label="EnableTestMode"),
            
        ]
        for par in pars:
            par.createPar(page)

        pass

