@echo off
chcp 65001 > nul
title Project BUKI - Server
echo ========================================================
echo   🔮 Project BUKI - Local LLM & TTS Virtual Companion
echo ========================================================
echo.
echo [*] Local URL:     http://localhost:8000
echo [*] Tailscale IP:  http://100.124.66.37:8000
echo [*] Funnel URL:    https://mother-goose.tail05cb80.ts.net:8443
echo.
cd /d "%~dp0..\src\backend"
python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause