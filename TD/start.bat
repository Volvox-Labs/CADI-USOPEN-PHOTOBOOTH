rem turn off echo
@echo off

IF EXIST "dep" (
  echo "dep exists"
) ELSE (
  CALL install-deps.cmd
)

IF EXIST ".env" (
  echo ".env exists"
) ELSE (
  COPY .env.sample .env
)

:: Copy missing env variables from .env.sample to .env, skipping comments
FOR /F "usebackq tokens=1* delims==" %%i IN (.env.sample) DO (
  IF NOT "%%i"=="" (
    IF NOT "%%i:~0,1"=="#" (
      FINDSTR /R /C:"^%%i=" .env >nul || ECHO %%i=%%j>>.env
    )
  )
)

:: TouchDesigner build numbers
set TOUCHVERSION=2023.12120

:: set our project file target
set TOEFILE="cadi-usopen-photobooth.toe"

:: set the rest of our paths for executables
set TOUCHDIR=%PROGRAMFILES%\Derivative\TouchDesigner.
set TOUCHEXE=\bin\TouchDesigner.exe

:: combine our elements so we have a single path to our TouchDesigner.exe
set TOUCHPATH="%TOUCHDIR%%TOUCHVERSION%%TOUCHEXE%"

IF EXIST %TOUCHPATH% (
  REM Do one thing
) ELSE (
  set TOUCHDIR=%PROGRAMFILES%\Derivative\TouchDesigner
  set TOUCHPATH="%TOUCHDIR%%TOUCHEXE%"
)

:: start our project file with the target TD installation
start "" %TOUCHPATH% %TOEFILE%
