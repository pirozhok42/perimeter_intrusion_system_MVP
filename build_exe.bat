@echo off
cd /d "%~dp0"

if not exist .venv (
    py -3.10 -m venv .venv
)

call .venv\Scripts\activate

pip install pyinstaller

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name PerimeterVision ^
  --add-data "configs;configs" ^
  --add-data "app;app" ^
  --collect-all ultralytics ^
  --collect-all supervision ^
  --collect-all torchvision ^
  --hidden-import cv2 ^
  --hidden-import torch ^
  --hidden-import torchvision ^
  run_gui.py

echo.
echo Build complete.
echo EXE path:
echo dist\PerimeterVision\PerimeterVision.exe
pause
