@echo off
title QuantumSafeVPN - Package for Kali Linux
cd /d "%~dp0"
echo =========================================================
echo   Creating Clean QuantumSafeVPN ZIP for Kali Linux...
echo =========================================================
python create_kali_zip.py
echo.
pause
