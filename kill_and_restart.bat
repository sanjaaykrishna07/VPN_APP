@echo off
title QuantumSafeVPN - Clean Restart
cd /d "%~dp0"
echo =================================================================
echo   Stopping any old zombie server instances on port 7000 & 8000...
echo =================================================================

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :7000 ^| findstr LISTENING') do (
    echo Killing stale process on port 7000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing stale process on port 8000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo =================================================================
echo   Starting FRESH QuantumSafeVPN Server & Web Dashboard...
echo =================================================================
echo.
python run.py
pause
