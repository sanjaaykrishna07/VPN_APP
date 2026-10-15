@echo off
title QuantumSafeVPN - Web Dashboard & VPN Server
cd /d "%~dp0"

echo =================================================================
echo   QuantumSafeVPN — Launching Post-Quantum Platform
echo =================================================================
echo.

:: 1. Clear any stuck background processes on ports 7000 & 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :7000 ^| findstr LISTENING 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Find Python executable (python or py)
set "PY_CMD="
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
) else (
    py --version >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PY_CMD=py"
    )
)

if "%PY_CMD%"=="" (
    echo [!] ERROR: Python was not found in your PATH.
    echo Please install Python 3.10+ or make sure Python is added to PATH.
    echo.
    pause
    exit /b 1
)

echo   [+] Using Python: %PY_CMD%
echo   🌐 Dashboard URL : http://127.0.0.1:8000 (or 8001 if 8000 is occupied)
echo   🔑 Default Login : admin / admin123
echo   📡 VPN Server    : Port 7000
echo.
echo =================================================================
echo.

%PY_CMD% run.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Encountered an error. Retrying with dependencies installation...
    %PY_CMD% -m pip install -r requirements.txt
    echo.
    %PY_CMD% run.py
)

pause
