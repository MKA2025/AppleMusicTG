#!/bin/bash

# Build Docker image
docker-compose build

# Create necessary directories if they don't exist
mkdir -p downloads temp cache config

# Copy example config if it doesn't exist
if [ ! -f config/config.json ]; then
    cp config/config.example.json config/config.json
    echo "Please edit config/config.json with your settings"
fi
