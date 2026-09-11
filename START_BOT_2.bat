@echo off
title CookieRun Classic Bot - Instance 2 (Port 8001)
cd /d "%~dp0\src"
echo ========================================================
echo   CookieRun Classic Bot - Starting Instance 2 (Port 8001)...
echo ========================================================
python run_web.py --port 8001 %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Cannot run Python or required packages are missing!
    echo Please run 'INSTALL.bat' first or make sure Python is installed and added to PATH.
    echo.
    pause
)
