#!/bin/bash

app_file="app.py"

screen -dmS f-m-session python3 "$app_file"

if [ $? -eq 0 ]; then
    echo "File Manager is running in screen session 'f-m-session'."
else
    echo "Failed to start File Manager."
    exit 1
fi
