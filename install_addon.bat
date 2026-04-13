@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

:: =================================================================
:: 1. 파일 복사 (Web Addon UI 파일)
:: =================================================================
echo [1/2] Web Addon UI 파일을 복사합니다...
echo.

REM --- 사용자의 Wwise 버전에 맞게 이 경로를 수정해야 할 수 있습니다. ---
set "WAAPI_Addon_Path=C:\Program Files (x86)\Audiokinetic\Wwise 2023.1.4.8496\Authoring\Data\Web\addons"
REM -------------------------------------------------------------

REM addon 폴더가 있는지 확인
if not exist "addon" (
    echo [오류] 'addon' 폴더를 찾을 수 없습니다. 스크립트가 툴의 원본 폴더에서 실행되고 있는지 확인하세요.
    pause
    exit /b 1
)

robocopy "addon" "%WAAPI_Addon_Path%\Wwise-Bus-Routing-Auditor" /E /NFL /NDL /NJH /NJS /nc /ns /np
if errorlevel 4 (
    echo [성공] Web Addon UI 파일이 아래 경로에 복사되었습니다.
    echo %WAAPI_Addon_Path%\Wwise-Bus-Routing-Auditor
) else (
    echo [오류] Web Addon UI 파일 복사에 실패했습니다.
    echo Wwise 설치 경로가 올바른지, 관리자 권한으로 실행했는지 확인해주세요.
    pause
    exit /b 1
)
echo.

:: =================================================================
:: 2. 메뉴 등록 (Command Addon JSON 파일 생성)
:: =================================================================
echo [2/2] Wwise Tools 메뉴에 명령을 등록합니다...
echo.

:: launch.bat 절대 경로 계산
set "LAUNCH_PATH=%~dp0launch.bat"

:: Add-ons\Commands 폴더 생성
set "ADDON_DIR=%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands"
if not exist "%ADDON_DIR%" mkdir "%ADDON_DIR%"

:: PowerShell을 이용해 JSON 파일 생성 (전체 경로 사용)
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command ^
    "$launch = '%LAUNCH_PATH:\\=\\\\%';" ^
    "$json = ConvertTo-Json @{version=1; commands=@(@{id='com.tools.bus-routing-auditor'; displayName='Bus Routing Auditor'; program=$launch; mainMenu=@{basePath='Tools'}})} -Depth 5;" ^
    "Set-Content -Path '%ADDON_DIR%\BusRoutingAuditor.json' -Value $json -Encoding UTF8"

if errorlevel 1 (
    echo [오류] Add-on 메뉴 등록에 실패했습니다. PowerShell 실행에 문제가 있을 수 있습니다.
    pause
    exit /b 1
)

echo [성공] Wwise Add-on 메뉴 등록 완료.
echo JSON 파일 위치: %ADDON_DIR%\BusRoutingAuditor.json
echo.
echo -----------------------------------------------------------------
echo.
echo 모든 설치 과정이 완료되었습니다!
echo.
echo Wwise가 이미 실행 중이라면, 메뉴에서 [Tools] -> [Reload Command Add-ons]를 선택하세요.
echo 또는 Wwise를 재시작하면 Tools 메뉴에 "Bus Routing Auditor"가 나타납니다.
echo.

pause
