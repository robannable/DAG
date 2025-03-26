@echo off
:: Activate virtual environment
call venv\Scripts\activate.bat

:: Run the application
streamlit run DAG.py

:: Pause if there's an error
pause 