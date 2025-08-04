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

:: BEGIN ENV VARIABLES 
set MODE=dev
set assets_path=D:\Cadi2025\assets\
set comfyui_url=http://localhost:8188
set comfyui_inputs_dir=C:/ComfyUI_windows_portable/ComfyUI_windows_portable/ComfyUI/input/
set comfyui_outputs_dir=C:/ComfyUI_windows_portable/ComfyUI_windows_portable/ComfyUI/output/
set monitor_index=1
set blackmagic_camera_index=0
set takeaways_render_dir=D:/Takeaway/renders/
set uploader_websocket_url=ws://localhost:9985
:: start our project file with the target TD installation
start "" %TOUCHPATH% %TOEFILE%
