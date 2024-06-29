#!/bin/bash

screen -dmS file-manager-session python3 app.py

if [ $? -eq 0 ]; then
    echo "File manager is running in screen session 'file-manager-session'."
else
    echo "Failed to start File manager."
    exit 1
fi
