$Host.UI.RawUI.WindowTitle = "Project BUKI - Server"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  🔮 Project BUKI - Local LLM & TTS Virtual Companion" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "`n[*] Local URL:     http://localhost:8000" -ForegroundColor Green
Write-Host "[*] Tailscale IP:  http://100.124.66.37:8000 (모바일 Z Fold8 접속용)" -ForegroundColor Yellow
Write-Host "[*] Funnel URL:    https://mother-goose.tail05cb80.ts.net" -ForegroundColor Yellow
Write-Host "`n서버를 구동합니다 (Ctrl+C 로 종료)...`n"

Set-Location "$PSScriptRoot\..\src\backend"
python -m uvicorn app:app --host 0.0.0.0 --port 8000