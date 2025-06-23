if not exist ".\dep" mkdir dep

if not exist ".\dep\python" mkdir dep\python

:: Update dependencies

:: make sure pip is up to date
py -3.11 -m pip install --user --upgrade pip

:: install requirements
py -3.11 -m pip install -r "./requirements.txt" --target="./dep/python" --upgrade
