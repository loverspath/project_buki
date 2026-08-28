# AGY Persistent Session Runner via psmux (Windows Terminal Multiplexer)
# Survives Mobile SSH disconnects, app switches, and smartphone sleep/lock screen!
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "AGY Persistent psmux Session"

$sessionName = "buki-agy"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  🛡️ AGY Persistent Session Manager (psmux + watchdog)" -ForegroundColor Cyan
Write-Host "  - Mobile SSH Disconnect-Proof & Lock-Screen Proof" -ForegroundColor Yellow
Write-Host "  - Auto-reconnects to running session on SSH reconnect" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Check if psmux is installed
$psmuxCmd = Get-Command psmux -ErrorAction SilentlyContinue
if (-not $psmuxCmd) {
    Write-Host "⚠️ psmux not found in PATH, falling back to direct watchdog loop..." -ForegroundColor Yellow
    & "$PSScriptRoot\run_agy_watchdog.ps1" $args
    exit
}

# Check if session already exists
$sessionList = & psmux ls 2>&1 | Out-String

if ($sessionList -match $sessionName) {
    Write-Host "🔄 Attaching to existing AGY session '$sessionName'..." -ForegroundColor Green
    & psmux attach -t $sessionName
} else {
    Write-Host "🚀 Spawning new persistent AGY session '$sessionName'..." -ForegroundColor Green
    & psmux new -s $sessionName "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\run_agy_watchdog.ps1`""
}
