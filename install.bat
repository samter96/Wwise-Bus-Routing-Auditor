@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
echo [Bus Routing Auditor] Installing...

set PYTHON_EXE=

for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYTHON_EXE (
        echo %%P | findstr /I "WindowsApps" >nul 2>&1
        if errorlevel 1 set PYTHON_EXE=%%P
    )
)

if not defined PYTHON_EXE (
    for /d %%D in ("%APPDATA%\uv\python\cpython-3.*-windows-x86_64-none") do (
        if not defined PYTHON_EXE (
            if exist "%%D\python.exe" set PYTHON_EXE=%%D\python.exe
        )
    )
)

if not defined PYTHON_EXE (
    py --version >nul 2>&1 && set PYTHON_EXE=py
)

if not defined PYTHON_EXE (
    echo [ERROR] Python not found.
    echo Install Python 3.10+ from https://www.python.org
    echo or install uv: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo Python: !PYTHON_EXE!
echo Creating virtual environment...
"!PYTHON_EXE!" -m venv .venv
if errorlevel 1 ( echo [ERROR] venv creation failed & pause & exit /b 1 )

echo Installing waapi-client...
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install waapi-client --quiet
if errorlevel 1 ( echo [ERROR] waapi-client install failed & pause & exit /b 1 )

echo.
echo [DONE] Installation complete.
echo Next: run install_addon.bat to register in Wwise Tools menu.
echo.
pause