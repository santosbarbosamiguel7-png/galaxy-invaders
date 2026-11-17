@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 galaxy_invaders_swapi.py
) else (
  python galaxy_invaders_swapi.py
)
echo.
echo Se houve erro, leia a mensagem acima.
pause
