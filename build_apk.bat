@echo off
title QuantumSafeVPN - Build Android APK
cd /d "%~dp0"
echo =========================================================
echo   Building QuantumSafeVPN Android Application (APK)...
echo =========================================================
python build_apk.py
echo.
pause
