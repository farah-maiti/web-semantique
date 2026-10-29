@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Executez d'abord INSTALLER.cmd avec une connexion Internet.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m scripts.serve
if errorlevel 1 pause
