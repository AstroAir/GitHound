@echo off
REM GitHound Services Manager
REM Cross-platform wrapper for services.py

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%\..\services.py" %*
