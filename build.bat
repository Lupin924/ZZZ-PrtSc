@echo off
chcp 65001 >nul
echo ========================================
echo ZZZ PrtSc Build Script
echo ========================================
echo.

cd /d "%~dp0"

echo Starting build...
echo.

python build.py

if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build complete!
echo.
pause
