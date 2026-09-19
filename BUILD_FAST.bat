@echo off
title CookieRun Bot - Build Fast EXE (PyInstaller)
cd /d "%~dp0"

echo ========================================================
echo   CookieRun Bot - Building Fast EXE (~2 minutes)
echo   Using PyInstaller
echo ========================================================
echo.

python build_exe.py --fast

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Check the log messages above.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [DONE] Build completed successfully!
echo Press any key to open the output folder...
pause > nul
explorer "%~dp0dist\CookieRun_Bot"
