#!/bin/bash

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create necessary directories
mkdir -p downloads temp config

# Copy example config if not exists
if [ ! -f config/config.json ]; then
    cp config/config.example.json config/config.json
    echo "Please edit config/config.json with your settings"
fi
