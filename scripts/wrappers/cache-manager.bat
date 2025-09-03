@echo off
REM GitHound Cache Manager
REM Cross-platform wrapper for cache-manager.py

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%\..\cache-manager.py" %*
