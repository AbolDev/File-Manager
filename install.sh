#!/bin/bash

red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
plain='\033[0m'

cur_dir=$(pwd)

# Check root
[[ $EUID -ne 0 ]] && echo -e "${red}Fatal error: ${plain} Please run this script with root privilege \n" && exit 1

# Check OS and set release variable
if [[ -f /etc/os-release ]]; then
    source /etc/os-release
    release=$ID
else
    echo "Failed to check the system OS, please contact the author!" >&2
    exit 1
fi
echo "The OS release is: $release"

install_dependencies() {
    case "${release}" in
    ubuntu | debian)
        apt-get update && apt-get install -y git screen python3-venv curl jq
        ;;
    centos | almalinux | rocky | oracle)
        yum -y update && yum install -y git screen python3-venv curl jq
        ;;
    fedora)
        dnf -y update && dnf install -y git screen python3-venv curl jq
        ;;
    arch | manjaro)
        pacman -Syu && pacman -Syu --noconfirm git screen python-virtualenv curl jq
        ;;
    opensuse-tumbleweed)
        zypper refresh && zypper install -y git screen python3-virtualenv curl jq
        ;;
    *)
        echo -e "${red}Your operating system is not supported by this script.${plain}\n"
        echo "Please ensure you are using one of the following supported operating systems:"
        echo "- Ubuntu"
        echo "- Debian"
        echo "- CentOS"
        echo "- Fedora"
        echo "- Arch Linux"
        echo "- Manjaro"
        echo "- OpenSUSE Tumbleweed"
        exit 1
        ;;
    esac
}

get_user_input() {
    local default_username=$(jq -r '.username' config.json)
    local default_password=$(jq -r '.password' config.json)
    local default_port=$(jq -r '.port' config.json)

    read -p "Enter username [default: ${default_username}]: " username
    username=${username:-$default_username}

    read -p "Enter password [default: ${default_password}]: " password
    password=${password:-$default_password}

    while true; do
        read -p "Enter port [default: ${default_port}]: " port
        port=${port:-$default_port}
        
        if [[ ! $port =~ ^[0-9]+$ ]]; then
            echo -e "${red}Invalid port number. Please enter a valid number.${plain}"
            continue
        fi

        if lsof -i:$port > /dev/null; then
            echo -e "${red}Port ${port} is in use. Please enter another port.${plain}"
        else
            break
        fi
    done

    jq --arg username "$username" --arg password "$password" --arg port "$port" \
       '.username=$username | .password=$password | .port=$port' config.json > config.tmp && mv config.tmp config.json
}

install_file_manager() {
    # Clone the repository
    cd /usr/local/
    if [[ -d "File-Manager" ]]; then
        echo -e "${yellow}File-Manager directory already exists. Removing...${plain}"
        rm -rf File-Manager
    fi

    echo -e "${green}Cloning the File-Manager repository...${plain}"
    git clone https://github.com/AbolDev/File-Manager.git
    cd File-Manager

    # Set up virtual environment
    echo -e "${green}Setting up virtual environment...${plain}"
    python3 -m venv myenv
    source myenv/bin/activate

    # Install the required dependencies
    echo -e "${green}Installing dependencies...${plain}"
    pip install -r requirements.txt

    # Get user input for config.json
    echo -e "${green}Configuring File Manager...${plain}"
    get_user_input

    # Start the web application
    echo -e "${green}Starting the web application...${plain}"
    sed -i 's/\r$//' start-app.sh
    bash start-app.sh

    # Get public IP address
    server_ip=$(curl -s ifconfig.me)

    echo -e "${green}File Manager installation finished, it is up and running now...${plain}"
    echo -e "Open your web browser and navigate to http://${server_ip}:${port} to access the application."
}

echo -e "${green}Running...${plain}"
install_dependencies
install_file_manager
