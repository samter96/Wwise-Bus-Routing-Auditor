@echo off
setlocal
cd /d "%~dp0"

echo [Bus Routing Auditor] Preparing Tauri build environment...

where npm >nul 2>&1 || (
    echo [ERROR] Node.js/npm is required.
    pause
    exit /b 1
)

where cargo >nul 2>&1 || (
    echo [ERROR] Rust/cargo is required for Tauri.
    pause
    exit /b 1
)

set "PYTHON_EXE="
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYTHON_EXE (
        echo %%P | findstr /I "WindowsApps" >nul 2>&1
        if errorlevel 1 set "PYTHON_EXE=%%P"
    )
)
if not defined PYTHON_EXE (
    py --version >nul 2>&1 && set "PYTHON_EXE=py"
)
if not defined PYTHON_EXE (
    echo [ERROR] Python 3.10+ is required.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" "%PYTHON_EXE%" -m venv .venv
if errorlevel 1 exit /b 1

echo [1/2] Installing Python backend dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip waapi-client --quiet
if errorlevel 1 exit /b 1

echo [2/2] Installing frontend dependencies...
call npm install
if errorlevel 1 exit /b 1

echo.
echo [DONE] Development setup complete.
echo Run launch.bat or: npm run tauri -- dev
echo.
pause
