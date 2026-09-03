@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run START_NWN_AI.bat once first to create the environment.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
python nwn_ai_gui.py
echo.
pause
