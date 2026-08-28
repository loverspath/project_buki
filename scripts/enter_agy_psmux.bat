@echo off
chcp 65001 > nul
title AGY Persistent psmux Session
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0enter_agy_psmux.ps1" %*
