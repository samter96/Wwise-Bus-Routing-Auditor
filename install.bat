@echo off
cd /d "%~dp0"
echo [Bus Routing Auditor] 설치 시작...

:: Python 확인 (일반 python → uv 관리 Python 순서로 탐색)
set PYTHON_EXE=
python --version >nul 2>&1 && set PYTHON_EXE=python
if not defined PYTHON_EXE (
    set PYTHON_EXE=%APPDATA%\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe
    if not exist "!PYTHON_EXE!" set PYTHON_EXE=
)
if not defined PYTHON_EXE (
    echo [오류] Python 을 찾을 수 없습니다.
    echo https://www.python.org 에서 Python 3.10 이상을 설치하거나,
    echo uv 를 설치하세요: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

:: 가상환경 생성
echo 가상환경 생성 중...
"!PYTHON_EXE!" -m venv .venv
if errorlevel 1 (
    echo [오류] 가상환경 생성 실패
    pause
    exit /b 1
)

:: 패키지 설치
echo waapi-client 설치 중...
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install waapi-client --quiet
if errorlevel 1 (
    echo [오류] waapi-client 설치 실패
    pause
    exit /b 1
)

echo.
echo [완료] 설치가 완료되었습니다.
echo 다음 단계: install_addon.bat 을 실행하면 Wwise Tools 메뉴에 등록됩니다.
echo.
pause
