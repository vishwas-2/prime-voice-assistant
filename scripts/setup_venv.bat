@echo off
REM Setup script for PRIME Voice Assistant virtual environment (Windows)

echo ==========================================
echo PRIME Voice Assistant - Setup Script
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Install PRIME in development mode
echo.
echo Installing PRIME in development mode...
pip install -e .

REM Download spaCy model
echo.
echo Downloading spaCy language model...
python -m spacy download en_core_web_sm

echo.
echo ==========================================
echo Setup complete!
echo ==========================================
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate.bat
echo.
echo To start PRIME, run:
echo   prime
echo.
pause
