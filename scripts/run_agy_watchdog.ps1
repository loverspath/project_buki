# AGY CLI Continuous Watchdog Runner (Anti-EOF & Auto-Restart for Mobile SSH / Long Sessions)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "AGY CLI - Persistent Watchdog"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  🛡️ AGY CLI Persistent Watchdog Loop Active" -ForegroundColor Cyan
Write-Host "  - Mobile SSH Fake EOF Prevention & Auto-Recovery Enabled" -ForegroundColor Yellow
Write-Host "  - Auto --continue on Reconnection Enabled" -ForegroundColor Yellow
Write-Host "  - To completely exit: Press Ctrl+C" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

$restartCount = 0

while ($true) {
    $startTime = Get-Date
    Write-Host "`n🚀 [$(Get-Date -Format 'HH:mm:ss')] Starting AGY session (Run #$($restartCount + 1))..." -ForegroundColor Green
    
    # On 1st run, pass user args. On subsequent auto-restarts, pass -c (--continue) if not already specified
    $cmdArgs = @()
    if ($args.Count -gt 0) {
        $cmdArgs += $args
    }
    if ($restartCount -gt 0 -and ($cmdArgs -notcontains "-c") -and ($cmdArgs -notcontains "--continue")) {
        $cmdArgs += "-c"
    }

    try {
        & agy $cmdArgs
    }
    catch {
        Write-Host "⚠️ [Exception Caught] $_" -ForegroundColor Red
    }

    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    $restartCount++

    Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] AGY process exited (Elapsed: $([math]::Round($duration, 1))s)." -ForegroundColor Yellow
    
    if ($duration -lt 2.0) {
        Write-Host "⏳ Short exit detected. Waiting 3 seconds before auto-respawn..." -ForegroundColor Gray
        Start-Sleep -Seconds 3
    } else {
        Start-Sleep -Milliseconds 500
    }
    
    Write-Host "🔄 Re-attaching to ongoing conversation (agy -c)..." -ForegroundColor Cyan
}
