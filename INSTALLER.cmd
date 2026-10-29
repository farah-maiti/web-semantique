@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\setup.py
) else (
  python scripts\setup.py
)
if errorlevel 1 (
  echo Installation non terminee. Consultez le message ci-dessus.
  pause
  exit /b 1
)
pause
