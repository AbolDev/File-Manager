#!/bin/bash

bot_file="app.py"

screen -dmS f-m-session python3 "$bot_file"

if [ $? -eq 0 ]; then
    echo "Bot is running in screen session 'f-m-session'."
else
    echo "Failed to start bot."
    exit 1
fi
