# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.project import ProjectEXT
from vvox_tdtools.parhelper import ParTemplate
import logging, os,sys
try:
    from td import root, project, absTime # type: ignore
except ModuleNotFoundError:
    from .td_mock import root, project, absTime
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Assuming td.absTime.frame is accessible here
        frame_number = absTime.frame
        record.frame_number = frame_number
        return super().format(record)
def createProjectLogger():

    # Initialize the logger.
    logger = logging.getLogger(root.var('PROJECT'))
    logger.setLevel(logging.DEBUG)

    # Create the log dir if not there
    if not os.path.exists(project.folder + '/logs/'):
        os.makedirs(project.folder + '/logs/')

    # Create file handler and set level.
    fh = logging.handlers.TimedRotatingFileHandler('logs/td-photobooth-' + root.var("photobooth_id") + '.log', when='midnight', backupCount=3)
    fh.setLevel(logging.DEBUG)

    # Create console handler and set level.
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)

    # Create formatter and add it to the handlers.
    formatter = CustomFormatter('%(asctime)s - Frame: %(frame_number)d - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger.
    logger.addHandler(fh)
    logger.addHandler(ch)


    print("Created Handler")
    logger.info('Logger initialized.')

class CadillacProjectEXT(ProjectEXT):
    def __init__(self, myop: OP, max_depth=10) -> None:
        ProjectEXT.__init__(self, myop)
        print(' Cadillac project extension i nit')
        self.Positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        self.main_window = root.op('main')
        self.status_view = root.op('window_status_view')

        self.Log_warnings = False
        self.Log_info = False
        createProjectLogger()
        self._enableLoggingOnExtensions()
        self.Logger.debug("CadillacProjectEXT initialized")
        pass
    
    def _enableLoggingOnExtensions(self):
        ops = op("/project1/output/opfind1")
        for op_row in ops.rows():
            # print(op_row[0], op_row[2])
            
            op_name = op_row[0].val
            if "_control" in  op_name or "_scene" in op_name:
                op_path = op_row[2].val
                op(op_path).par.Logtextport = True
                op(op_path).par.Debug = True
            
        pass