@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "LAUNCH_PATH=%~dp0launch.bat"
set "ADDON_DIR=%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands"

if not exist "%ADDON_DIR%" mkdir "%ADDON_DIR%"

powershell -NoProfile -Command "$launch = '%LAUNCH_PATH%'; $json = ConvertTo-Json @{version=1; commands=@(@{id='com.tools.bus-routing-auditor'; displayName='Bus Routing Auditor'; program=$launch; mainMenu=@{basePath='Tools'}})} -Depth 5; Set-Content -Path '%ADDON_DIR%\BusRoutingAuditor.json' -Value $json -Encoding UTF8"

if errorlevel 1 (
    echo [ERROR] Add-on file creation failed.
    pause
    exit /b 1
)

echo.
echo [DONE] Wwise Add-on registered:
echo   %ADDON_DIR%\BusRoutingAuditor.json
echo.
echo If Wwise is running: Tools ^> Reload Command Add-ons
echo Otherwise restart Wwise to see "Bus Routing Auditor" in the Tools menu.
echo.
pause
