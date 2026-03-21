@echo off
echo Running Jarvis X Tests...
echo.

if not exist venv (
    echo Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
venv\Scripts\python.exe test_jarvis.py
pause
