@echo off
title ?? Project BUKI - Master Server & Live Health Dashboard
chcp 65001 >nul
cd /d "C:\Users\rerun\opendcmart\projects\project_buki"

echo ============================================================
echo   ?? Project BUKI Master Launcher
echo   Starting Ollama, GPT-SoVITS, Chatterbox, and BUKI Web Server...
echo ============================================================

set PYTHONIOENCODING=utf-8
"C:\Python314\python.exe" "scripts\master_runner.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ? Server exited with code %ERRORLEVEL%.
    pause
)