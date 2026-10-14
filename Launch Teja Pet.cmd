@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0.runtime;%~dp0teja-pet"
where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "%~dp0launch.pyw" %*
  exit /b
)
echo Python is required. Install Python, then run pip install pygame.
pause
