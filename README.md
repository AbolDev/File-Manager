# File-Manager

## Introduction

File-Manager is a web application designed to help you manage your files easily through a web interface. 

## Features

- User-friendly interface
- Secure login
- Display all files in the system
- Open folders and display their contents
- Download files
- Upload files (single and multiple)
- Create folders
- Rename files and folders
- Delete files and folders

## Installation

To install and run the File-Manager project, execute the following command:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/AbolDev/File-Manager/master/install.sh)
```

## Configuration

During the installation, you will be prompted to set the following:

- **Username**: The username for logging into the application (default: `admin`).
- **Password**: The password for logging into the application (default: `12345`).
- **Port**: The port on which the application will run (default: `8000`).

If you want to keep the default values, just press Enter when prompted.

## Usage

Once the installation is complete, the application will be running in a screen session. Open your web browser and navigate to:

```
http://<server_ip>:<port>
```

Replace `<server_ip>` with your server's public IP address and `<port>` with the port you specified during installation.

## Recommended OS

For the best experience, it is recommended to use one of the following operating systems:

- Ubuntu 20.04+
- Debian 11+
- CentOS 8+
- Fedora 36+
- Arch Linux
- Manjaro
- AlmaLinux 9+
- Rocky Linux 9+
- Oracle Linux 8+

## Notes

- Ensure the specified port is not in use.
- For security reasons, it is recommended to change the default username and password.

## License

This project is licensed under the MIT License.
