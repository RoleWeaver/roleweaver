@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "nwn_ai_gui.py"
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "nwn_ai_gui.py"
    exit /b %errorlevel%
)

echo Role Weaver virtual environment not found.
echo Run Install_RoleWeaver.bat first.
pause
