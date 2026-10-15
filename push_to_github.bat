@echo off
cd /d "%~dp0"
echo ========================================================
echo   Pushing QuantumSafe VPN to GitHub
echo   Repository: https://github.com/sanjaaykrishna07/VPN_APP.git
echo ========================================================
echo.
"C:\Program Files\Git\cmd\git.exe" push -u origin main
echo.
pause
