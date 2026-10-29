@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Executez d'abord INSTALLER.cmd.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m scripts.build_ontology
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m scripts.reason
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m webapp.queries
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pytest -q --disable-warnings --basetemp runtime\test-temp --junitxml=validation\tests.xml
if errorlevel 1 goto :error
echo Validation terminee. Redemarrez Fuseki si le corpus a change.
pause
exit /b 0
:error
echo Validation interrompue. Corrigez l'erreur avant la demonstration.
pause
exit /b 1
