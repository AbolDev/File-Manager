#!/bin/bash

red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
plain='\033[0m'

config_file="/usr/local/File-Manager/config.json"
service_name="file-manager.service"

# Function to show current status
show_status() {
    username=$(jq -r '.username' "$config_file")
    password=$(jq -r '.password' "$config_file")
    port=$(jq -r '.port' "$config_file")
    
    if systemctl is-active --quiet $service_name; then
        status="${green}Running${plain}"
    else
        status="${red}Stopped${plain}"
    fi
    
    echo -e "\n${yellow}Current File Manager Configuration:${plain}"
    echo -e "Username: ${green}$username${plain}"
    echo -e "Password: ${green}$password${plain}"
    echo -e "Port: ${green}$port${plain}"
    echo -e "Status: $status\n"
}

# Function to start the application
start_app() {
    if systemctl is-active --quiet $service_name; then
        echo -e "${yellow}The app is already running.${plain}"
    else
        systemctl start $service_name
        echo -e "${green}App started successfully.${plain}"
    fi
}

# Function to stop the application
stop_app() {
    if systemctl is-active --quiet $service_name; then
        systemctl stop $service_name
        echo -e "${green}App stopped successfully.${plain}"
    else
        echo -e "${yellow}The app is already stopped.${plain}"
    fi
}

# Function to restart the application
restart_app() {
    systemctl restart $service_name
    echo -e "${green}App restarted successfully.${plain}"
}

# Function to change username
change_username() {
    read -p "Enter new username: " new_username
    jq --arg username "$new_username" '.username = $username' "$config_file" > config.tmp && mv config.tmp "$config_file"
    echo -e "${green}Username updated to $new_username.${plain}"
    restart_app
}

# Function to change password
change_password() {
    read -p "Enter new password: " new_password
    jq --arg password "$new_password" '.password = $password' "$config_file" > config.tmp && mv config.tmp "$config_file"
    echo -e "${green}Password updated successfully.${plain}"
    restart_app
}

# Function to check if a port is free
is_port_free() {
    if lsof -i:"$1" > /dev/null; then
        return 1
    else
        return 0
    fi
}

# Function to change port
change_port() {
    while true; do
        read -p "Enter new port: " new_port
        if [[ ! $new_port =~ ^[0-9]+$ ]]; then
            echo -e "${red}Invalid port number. Please enter a valid number.${plain}"
            continue
        fi

        if is_port_free "$new_port"; then
            jq --arg port "$new_port" '.port = $port' "$config_file" > config.tmp && mv config.tmp "$config_file"
            echo -e "${green}Port updated to $new_port.${plain}"
            restart_app
            break
        else
            echo -e "${red}Port $new_port is in use. Please enter another port.${plain}"
        fi
    done
}

# Main menu
while true; do
    show_status
    echo -e "${yellow}Please choose an option:${plain}"
    echo -e "1) Start the app"
    echo -e "2) Stop the app"
    echo -e "3) Restart the app"
    echo -e "4) Change username"
    echo -e "5) Change password"
    echo -e "6) Change port"
    echo -e "7) Exit"

    read -p "Enter your choice [1-7]: " choice

    case $choice in
        1) start_app ;;
        2) stop_app ;;
        3) restart_app ;;
        4) change_username ;;
        5) change_password ;;
        6) change_port ;;
        7) echo -e "${green}Exiting...${plain}" && exit 0 ;;
        *) echo -e "${red}Invalid choice. Please select a valid option.${plain}" ;;
    esac
done
