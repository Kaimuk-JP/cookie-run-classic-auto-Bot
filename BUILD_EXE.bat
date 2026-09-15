@echo off
title CookieRun Bot - Build Protected Native EXE (Nuitka)
cd /d "%~dp0"

echo ========================================================
echo   CookieRun Bot - Building Protected Native EXE
echo   Using Nuitka + Zig C-Compiler
echo ========================================================
echo.

python build_exe.py

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
    