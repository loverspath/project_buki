@echo off
chcp 65001 > nul
title AGY Persistent Watchdog
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_agy_watchdog.ps1" %*
