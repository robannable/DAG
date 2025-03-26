#!/bin/bash

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/Scripts/activate

# Install requirements
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "PERPLEXITY_API_KEY=your_api_key_here" > .env
    echo "Please edit .env file with your Perplexity API key"
fi

echo "Setup complete! To run the application:"
echo "1. Activate the virtual environment: source venv/Scripts/activate"
echo "2. Run the app: streamlit run diegetic_generator.py" 