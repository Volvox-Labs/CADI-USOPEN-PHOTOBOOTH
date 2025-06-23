@echo off
echo Checking for updates to ComfyUI Docker image...
echo Starting ComfyUI Docker container...

docker run -it --rm      --name comfyui-sketch      --gpus all      -p 8188:8188      -p 7860:7860      -v "%~dp0:/root"      -e CLI_ARGS="--fast"      wenyiii/comfyui-boot:cu124-slim

echo Container stopped.
pause
