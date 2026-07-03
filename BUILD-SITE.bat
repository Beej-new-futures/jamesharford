@echo off
rem Regenerates the site pages after adding/changing folders in content\projects\
cd /d "%~dp0"
python scripts\build.py
echo.
echo Done - now commit and push in GitHub Desktop to deploy.
pause
