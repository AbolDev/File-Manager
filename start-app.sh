#!/bin/bash

app_file="app.py"

# Start the Flask app in a detached screen session
screen -dmS f-m-session python3 "$app_file"

# Check if Flask started successfully
if [ $? -eq 0 ]; then
    # Wait for a moment to allow Flask to start and print initial messages
    sleep 2
    # Get the output from screen logs that contains Flask startup messages
    screen_logs=$(screen -S f-m-session -X logs)
    # Print the Flask startup messages
    echo "$screen_logs"
else
    echo "Failed to start File Manager."
    exit 1
fi
