@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Not set up yet. Double-click setup.bat first.
  pause
  exit /b 1
)
echo Starting CV Screener... your browser will open in a moment.
.venv\Scripts\python app.py
pause
