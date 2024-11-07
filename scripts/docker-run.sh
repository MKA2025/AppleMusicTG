#!/bin/bash

# Start the bot in detached mode
docker-compose up -d

# Show logs
docker-compose logs -f
