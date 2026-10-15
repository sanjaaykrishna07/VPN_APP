@echo off
title QuantumSafeVPN - Production Server & Bridge Launcher
cd /d "%~dp0"

echo =================================================================
echo   QuantumSafeVPN — Server & Bridge Launcher for Review Demo
echo =================================================================
echo.

REM 1. Kill any zombie python processes on port 7000 on Windows
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :7000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM 2. Ensure WSL Linux server is active
echo [*] Checking WSL2 Linux VPN Server status...
wsl -u root ps aux | findstr "tunnel_server.py" >nul 2>&1
if errorlevel 1 (
    echo [*] Starting Linux tunnel_server inside WSL2...
    start /b wsl -u root bash -c "cd /home/sanjaay_krishna/QuantumSafeVPN && venv/bin/python vpn/tunnel_server.py"
    timeout /t 2 >nul
) else (
    echo [+] Linux tunnel_server is already running in WSL2!
)

REM 3. Launch Windows-to-WSL Bridge
echo.
echo =================================================================
echo   Starting Windows-to-WSL Bridge on port 7000...
echo =================================================================
python wsl_bridge.py

pause
