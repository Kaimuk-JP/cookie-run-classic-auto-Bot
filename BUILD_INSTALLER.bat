@echo off
title CookieRun Bot - Windows Installer Builder
cd /d "%~dp0"

echo ========================================================
echo   CookieRun Classic Bot - Windows Installer (.exe) Builder
echo ========================================================
echo.

python build_installer.py --force-rebuild

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to build Windows Installer!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo [DONE] Installer created successfully!
echo Opening folder...
echo ========================================================
explorer /select,"%~dp0dist_installer\CookieRunBot_Setup_v2.0.0.exe"
