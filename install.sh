#!/bin/bash

red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
plain='\033[0m'

cur_dir=$(pwd)
use_defaults=false
username_param=""
password_param=""
port_param=""

# Parse input arguments
for arg in "$@"; do
    case $arg in
        --default)
            use_defaults=true
            ;;
        --username=*)
            username_param="${arg#*=}"
            ;;
        --password=*)
            password_param="${arg#*=}"
            ;;
        --port=*)
            port_param="${arg#*=}"
            ;;
        *)
            echo -e "${red}Unknown option: $arg${plain}"
            exit 1
            ;;
    esac
done

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

    if [[ "$use_defaults" == true ]]; then
        username=${username_param:-$default_username}
        password=${password_param:-$default_password}
        port=${port_param:-$default_port}
    else
        username=${username_param:-$default_username}
        password=${password_param:-$default_password}
        port=${port_param:-$default_port}

        # If no username is passed via argument, prompt the user
        if [[ -z "$username_param" ]]; then
            read -p "Enter username [default: ${default_username}]: " username
            username=${username:-$default_username}
        fi

        # If no password is passed via argument, prompt the user
        if [[ -z "$password_param" ]]; then
            read -p "Enter password [default: ${default_password}]: " password
            password=${password:-$default_password}
        fi

        # If no port is passed via argument, prompt the user
        if [[ -z "$port_param" ]]; then
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
        fi
    fi

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

create_systemd_service() {
    echo -e "${green}Creating systemd service for File Manager...${plain}"
    
    # Create the systemd service file
    cat <<EOF > /etc/systemd/system/file-manager.service
[Unit]
Description=File Manager Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/File-Manager
ExecStart=/usr/local/File-Manager/myenv/bin/python3 /usr/local/File-Manager/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd, enable and start the service
    systemctl daemon-reload
    systemctl enable file-manager.service
    systemctl start file-manager.service

    echo -e "${green}File Manager service created and enabled to start on boot.${plain}"
}

create_file_manager_command() {
    echo -e "${green}Creating 'file-manager' command...${plain}"

    # Create the file-manager script directly in /usr/local/bin/
    cat <<EOF > /usr/local/bin/file-manager
#!/bin/bash

config_file="/usr/local/File-Manager/config.json"

while true; do
    # Check service status
    # Uncomment the next lines if you want to display service status
    # if systemctl is-active --quiet file-manager.service; then
    #     status="\e[32mRunning\e[0m"  # Green color for active
    # else
    #     status="\e[31mStopped\e[0m"  # Red color for inactive
    # fi

    # For now, always assume the service is running
    status="\e[32mRunning\e[0m"

    username=\$(jq -r '.username' \$config_file)
    password=\$(jq -r '.password' \$config_file)
    port=\$(jq -r '.port' \$config_file)

    echo ""
    echo -e "File Manager Status: \$status"
    echo "Username: \$username"
    echo "Password: \$password"
    echo "Port: \$port"
    echo ""
    echo "Options:"
    echo "1- Start File Manager"
    echo "2- Stop File Manager"
    echo "3- Restart File Manager"
    echo "4- Change Username"
    echo "5- Change Password"
    # echo "6- Change Port"
    echo "0- Exit"

    read -p "Choose an option: " option

    case \$option in
        1)
            if ! systemctl is-active --quiet file-manager.service; then
                systemctl start file-manager.service
                echo -e "\e[32mFile Manager started successfully.\e[0m"
            else
                echo -e "\e[33mFile Manager is already running.\e[0m"
            fi
            ;;
        2)
            if systemctl is-active --quiet file-manager.service; then
                systemctl stop file-manager.service
                echo -e "\e[32mFile Manager stopped successfully.\e[0m"
            else
                echo -e "\e[33mFile Manager is already stopped.\e[0m"
            fi
            ;;
        3)
            systemctl restart file-manager.service
            echo -e "\e[32mFile Manager restarted successfully.\e[0m"
            ;;
        4)
            read -p "Enter new username: " new_username
            jq --arg new_username "\$new_username" '.username=\$new_username' \$config_file > config.tmp && mv config.tmp \$config_file
            echo -e "\e[32mUsername changed successfully.\e[0m"
            ;;
        5)
            read -p "Enter new password: " new_password
            jq --arg new_password "\$new_password" '.password=\$new_password' \$config_file > config.tmp && mv config.tmp \$config_file
            echo -e "\e[32mPassword changed successfully.\e[0m"
            ;;
        # 6)
        #     while true; do
        #         read -p "Enter new port: " new_port
        #         if [[ ! \$new_port =~ ^[0-9]+$ ]]; then
        #             echo -e "\e[31mInvalid port number. Please enter a valid number.\e[0m"
        #             continue
        #         fi
        #         if lsof -i:\$new_port > /dev/null; then
        #             echo -e "\e[31mPort \$new_port is in use. Please enter another port.\e[0m"
        #         else
        #             # Stop the current running app
        #             echo -e "\e[32mStopping File Manager...\e[0m"
        #             systemctl stop file-manager.service

        #             # Update port in config file
        #             jq --arg new_port "\$new_port" '.port=\$new_port' \$config_file > config.tmp && mv config.tmp \$config_file

        #             # Restart the app
        #             echo -e "\e[32mStarting File Manager...\e[0m"
        #             systemctl start file-manager.service
        #             echo -e "\e[32mPort changed and File Manager restarted successfully.\e[0m"
        #             break
        #         fi
        #     done
        #     ;;
        0)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
done
EOF

    # Make the script executable
    chmod +x /usr/local/bin/file-manager

    echo -e "${green}Command 'file-manager' created successfully. You can now run 'file-manager' to access the management menu.${plain}"
}

echo -e "${green}Running...${plain}"
install_dependencies
install_file_manager
create_systemd_service
create_file_manager_command