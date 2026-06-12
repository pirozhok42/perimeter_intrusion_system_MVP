@echo off
cd /d "%~dp0"
if not exist .venv (
    echo Creating virtual environment...
    py -3.10 -m venv .venv
)
call .venv\Scripts\activate
python -m app.gui.main
pause
