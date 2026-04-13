@echo off
setlocal EnableDelayedExpansion

:: =================================================================
:: 1. 설치된 Wwise 버전 자동 탐색 및 사용자 선택
:: =================================================================
echo [1/3] PC에 설치된 Wwise 버전을 찾고 있습니다...
echo.

set "AudiokineticPath=C:\Program Files (x86)\Audiokinetic"
if not exist "%AudiokineticPath%" (
    echo [오류] Audiokinetic 설치 폴더를 찾을 수 없습니다.
    echo 경로: %AudiokineticPath%
    pause
    exit /b 1
)

set "count=0"
echo 설치할 Wwise 버전을 선택하세요:
echo -------------------------------------------------
for /d %%d in ("%AudiokineticPath%\Wwise 202*") do (
    if exist "%%d\Authoring\Data\Web\addons\" (
        set /a count+=1
        set "WwisePath[!count!]=%%d\Authoring\Data\Web\addons"
        echo [!count!] %%~nd
    )
)
echo -------------------------------------------------

if %count% equ 0 (
    echo [오류] 설치된 Wwise 버전을 찾지 못했습니다.
    pause
    exit /b 1
)

:choice
set /p "choice=번호를 입력하세요: "
if not defined WwisePath[%choice%] (
    echo 잘못된 번호입니다. 다시 입력해주세요.
    goto :choice
)

set "WAAPI_Addon_Path=!WwisePath[%choice%]!"
echo.

:: =================================================================
:: 2. 파일 복사 (Web Addon UI 파일)
:: =================================================================
echo [2/3] Web Addon UI 파일을 복사합니다...
cd /d "%~dp0"
if not exist "addon" (
    echo [오류] 'addon' 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)

robocopy "addon" "!WAAPI_Addon_Path!\Wwise-Bus-Routing-Auditor" /E /NFL /NDL /NJH /NJS /nc /ns /np > nul
if not errorlevel 4 (
    echo [오류] Web Addon UI 파일 복사에 실패했습니다.
    echo 관리자 권한으로 스크립트를 실행했는지 확인해주세요.
    pause
    exit /b 1
)
echo [성공] Web Addon UI 파일 복사 완료.
echo.

:: =================================================================
:: 3. 메뉴 등록 (Command Addon JSON 파일 생성)
:: =================================================================
echo [3/3] Wwise Tools 메뉴에 명령을 등록합니다...

set "LAUNCH_PATH=%~dp0launch.bat"
set "ADDON_DIR=%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands"
if not exist "%ADDON_DIR%" mkdir "%ADDON_DIR%"

"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command ^
    "$launch = '%LAUNCH_PATH:\\=\\\\%';" ^
    "$json = ConvertTo-Json @{version=1; commands=@(@{id='com.tools.bus-routing-auditor'; displayName='Bus Routing Auditor'; program=$launch; mainMenu=@{basePath='Tools'}})} -Depth 5;" ^
    "Set-Content -Path '%ADDON_DIR%\BusRoutingAuditor.json' -Value $json -Encoding UTF8"

if errorlevel 1 (
    echo [오류] Add-on 메뉴 등록에 실패했습니다.
    pause
    exit /b 1
)

echo [성공] Wwise Add-on 메뉴 등록 완료.
echo.
echo -----------------------------------------------------------------
echo.
echo 모든 설치 과정이 완료되었습니다!
echo Wwise를 재시작하면 Tools 메뉴에 "Bus Routing Auditor"가 나타납니다.
echo.
pause
