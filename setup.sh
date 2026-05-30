#!/bin/bash

# Create virtual environment
python -m venv venv

# Create artefacts directory
mkdir -p artefacts

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
    echo "Please edit .env file with your Anthropic API key"
fi

echo "Setup complete! To run the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the app: streamlit run DAG.py"
