@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

:: launch.bat 절대 경로 계산
set "LAUNCH_PATH=%~dp0launch.bat"

:: Add-ons\Commands 폴더 생성
set "ADDON_DIR=%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands"
if not exist "%ADDON_DIR%" mkdir "%ADDON_DIR%"

:: JSON 내 백슬래시 이스케이프 (PowerShell 에 위임)
powershell -NoProfile -Command ^
    "$launch = '%LAUNCH_PATH:\=\\%';" ^
    "$json = ConvertTo-Json @{version=1; commands=@(@{id='com.tools.bus-routing-auditor'; displayName='Bus Routing Auditor'; program=$launch; mainMenu=@{basePath='Tools'}})} -Depth 5;" ^
    "Set-Content -Path '%ADDON_DIR%\BusRoutingAuditor.json' -Value $json -Encoding UTF8"

if errorlevel 1 (
    echo [오류] Add-on 파일 생성 실패
    pause
    exit /b 1
)

echo.
echo [완료] Wwise Add-on 등록 완료:
echo   %ADDON_DIR%\BusRoutingAuditor.json
echo.
echo Wwise 가 실행 중이라면:
echo   메뉴 ^> Tools ^> Reload Command Add-ons
echo 또는 Wwise 를 재시작하면 Tools 메뉴에 "Bus Routing Auditor" 가 나타납니다.
echo.
pause
