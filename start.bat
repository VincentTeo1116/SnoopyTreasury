@echo off
echo   GLOBAL TREASURY AGENT - LAUNCHER
echo.

echo Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed
echo.

echo Starting Streamlit application...
echo.
echo   Opening dashboard in your browser...
echo.

streamlit run streamlit_app.py

pause