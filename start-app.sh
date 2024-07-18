#!/bin/bash

app_file="app.py"

# Start the Flask app in a detached screen session
screen -dmS f-m-session python3 "$app_file"

# Check if Flask started successfully
if [ $? -eq 0 ]; then
    # Wait for a moment to allow Flask to start and print initial messages
    sleep 2
    # Send a command to the screen session to print its log
    screen -S f-m-session -X stuff $'\n'
else
    echo "Failed to start File Manager."
    exit 1
fi
