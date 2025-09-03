@echo off
REM GitHound Quick Start
REM Cross-platform wrapper for quick-start.py

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%\..\quick-start.py" %*
