# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
from vvox_tdtools.parhelper import ParTemplate
try:
    # import td
    from td import OP # type: ignore
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, ParMode  #pylint: disable=ungrouped-imports



class ProjectMetricsEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self._createMetricsPage()
        pass

    def OnInit(self):
        # return False if initialization fails
        return True


    def _createMetricsPage(self) -> None:
        page = self.GetPage('Metrics')
        # all prometheus metrics must have a label that is all lower case snake case
        status_view_page_par = ParTemplate('Statusviewpageindex', par_type='Int', label='status_view_page_index')
        # It's best practice to create a metric paramater on a component like 'status_view'
        # and then simply refer to that parameter with an expression in this component
        status_view_page_par.mode = ParMode.EXPRESSION #pylint: disable=used-before-assignment
        status_view_page_par.expr = "op.status_view.par.Statusviewpageindex.eval()"

        pars = [
            status_view_page_par

        ]
        for par in pars:
            par.createPar(page)

        pass

