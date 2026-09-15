@echo off
title CookieRun Bot - Desktop Launcher
cd /d "%~dp0"

echo ========================================================
echo   CookieRun Classic Bot - Desktop GUI Launcher
echo ========================================================
echo.

python src\gui_launcher.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Cannot run GUI Launcher!
    pause
)
