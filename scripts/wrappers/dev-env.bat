@echo off
REM GitHound Development Environment Manager
REM Cross-platform wrapper for dev-env.py

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%\..\dev-env.py" %*
