@echo off
cd /d "%~dp0"
echo Setting up (only needed once)...
set PY=
python --version >nul 2>&1 && set PY=python
if not defined PY py --version >nul 2>&1 && set PY=py
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
if not defined PY for /d %%D in ("%ProgramFiles%\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
if defined PY echo Using Python: %PY%
if not defined PY (
  echo.
  echo SETUP FAILED: Python is not installed.
  echo Install it from https://www.python.org/downloads/
  echo and tick "Add Python to PATH" on the first screen. Then run setup.bat again.
  pause
  exit /b 1
)
%PY% -m venv .venv
if errorlevel 1 (
  echo.
  echo SETUP FAILED: could not create the .venv folder. Delete .venv if it exists and run setup.bat again.
  pause
  exit /b 1
)
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo SETUP FAILED: could not download the tool's parts. Check your internet and run setup.bat again.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env >nul
echo.
echo Setup done. Now open the .env file and paste your API key.
pause
