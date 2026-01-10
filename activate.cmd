@echo off

if exist ".venv\Scripts\activate.bat" (
    echo Monorepo configuration, activating venv from current directory
    call ".venv\Scripts\activate.bat"
    goto :eof
)

if exist "..\.venv\Scripts\activate.bat" (
    echo Multirepo configuration, activating venv from parent directory
    call "..\.venv\Scripts\activate.bat"
    goto :eof
)

echo ERROR: No .venv found in current or parent directory
