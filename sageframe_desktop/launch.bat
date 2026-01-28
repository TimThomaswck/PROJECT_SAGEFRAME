@echo off
REM SageFrame Desktop Application Launcher
REM 
REM This script properly launches the SageFrame desktop app
REM using the correct entry point.

cd /d "%~dp0"
python -m app

REM If app crashes, keep window open to see error
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
