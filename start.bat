@echo off
REM Events Paradise Event Management System
REM Windows Startup Script

echo ============================================
echo Events Paradise - Event Management System
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    pause
    exit /b 1
)

echo.
echo Starting application...
echo Access the application at: http://localhost:5000
echo Default admin login: admin / admin123
echo.
echo Press Ctrl+C to stop the server
echo ----------------------------------------

REM Run the application
python run.py

pause