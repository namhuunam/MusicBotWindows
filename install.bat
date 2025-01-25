
@echo off
echo Installing required libraries globally...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)

:: Install required libraries globally
echo Installing libraries from requirements.txt...
pip install -r requirements.txt

echo Installation complete. All libraries are installed globally.
pause
