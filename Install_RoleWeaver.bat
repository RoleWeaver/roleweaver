@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo Python was not found.
        echo Install Python 3 for Windows, then run this installer again.
        pause
        exit /b 1
    )
    set "PY=python"
)

echo Creating Role Weaver virtual environment...
%PY% -m venv .venv
if %errorlevel% neq 0 goto :fail

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if %errorlevel% neq 0 goto :fail

pip install -r requirements.txt
if %errorlevel% neq 0 goto :fail

echo.
echo Role Weaver installation is ready.
echo Run RoleWeaver.bat to start.
pause
exit /b 0

:fail
echo.
echo Installation failed. Review the error messages above.
pause
exit /b 1
