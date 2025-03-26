@echo off
echo Setting up Diegetic Artefact Generator...

:: Create virtual environment
python -m venv venv

:: Create artefacts directory
mkdir artefacts

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install requirements
pip install -r requirements.txt

:: Check if .env file exists and create if not
if not exist .env (
    echo Creating .env file...
    echo PERPLEXITY_API_KEY=your_api_key_here > .env
    echo OPENAI_API_KEY=your_api_key_here >> .env
    echo ANTHROPIC_API_KEY=your_api_key_here >> .env
    echo Please edit .env file with your API keys
)

echo Setup complete! To run the application:
echo 1. Make sure your virtual environment is activated: venv\Scripts\activate.bat
echo 2. Run the app: streamlit run DAG.py

:: Pause to keep window open
pause 