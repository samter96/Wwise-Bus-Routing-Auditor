@echo off
setlocal
cd /d "%~dp0"

set "RELEASE_EXE=src-tauri\target\release\bus-routing-auditor.exe"
if exist "%RELEASE_EXE%" (
    start "" "%RELEASE_EXE%"
    exit /b 0
)

where npm >nul 2>&1 || (
    echo [ERROR] Node.js/npm is required to run the Tauri development build.
    pause
    exit /b 1
)

call npm run tauri -- dev
