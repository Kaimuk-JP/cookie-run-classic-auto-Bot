@echo off
title CookieRun Classic Bot - Web Dashboard
cd /d "%~dp0\src"
echo ========================================================
echo   CookieRun Classic Bot - Starting Web Dashboard...
echo ========================================================
python run_web.py
if %ERRORLEVEL% NEQ 0 (
    if %ERRORLEVEL% NEQ -1073741510 (
        echo.
        echo บอทหยุดการทำงาน (รหัสสถานะ: %ERRORLEVEL%)
        echo หากพบปัญหา กรุณารัน 'INSTALL.bat' หรือตรวจสอบ Python
        echo.
        pause
    )
)
