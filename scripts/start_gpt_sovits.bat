@echo off
chcp 65001 > nul
echo ========================================================
echo   Project BUKI - GPT-SoVITS Zero-Shot Neural TTS Server
echo ========================================================
echo.
echo [1/2] Setting environment paths...
set PATH=%PATH%;C:\Users\rerun\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin;C:\Users\rerun\AppData\Local\hermes\bin

cd /d C:\Users\rerun\opendcmart\tools\GPT-SoVITS

if not exist .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not found at C:\Users\rerun\opendcmart\tools\GPT-SoVITS\.venv
    pause
    exit /b 1
)

echo [2/2] Starting GPT-SoVITS API Server on port 9880...
echo.
echo Server Endpoint: http://127.0.0.1:9880
echo.
.\.venv\Scripts\python.exe api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
pause
