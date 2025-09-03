@echo off
REM GitHound Health Check
REM Cross-platform wrapper for health-check.py

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%\..\health-check.py" %*
