:: Update dependencies

:: make sure pip is up to date
py -3.11 -m pip install --user --upgrade pip
py -3.11 -m pip install requests
py -3.11 -m pip install PyYAML

:: Exported from TDPyEnvManager version 1.3.8
set TD_INSTALL_PATH=C:\Program Files\Derivative\TouchDesigner
set TD_PYENVMANAGER_MODE=Python vEnv
set TD_PYENVMANAGER_ENVPATH=./
set TD_PYENVMANAGER_ENVNAME=vvox_td_py_env
set TD_PYENVMANAGER_PYTHONVERSION=3.11
set TOUCH_APP_LOG_LEVEL=INFO

py -3.11 "./scripts/TDPyEnvManagerHelper.py" --mode "%TD_PYENVMANAGER_MODE%" --installPath "%TD_PYENVMANAGER_ENVPATH%" --envName "%TD_PYENVMANAGER_ENVNAME%" --pythonVersion "%TD_PYENVMANAGER_PYTHONVERSION%" --keepInstaller