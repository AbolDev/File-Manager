### File-Manager

## Installation

To run this project locally, follow these steps:

1. Install necessary packages:
   ```bash
   sudo apt update
   sudo apt install git
   sudo apt install screen
   sudo apt install python3-venv
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/AbolDev/File-Manager.git
   cd File-Manager
   ```

3. Set up a virtual environment:
   ```bash
   python3 -m venv myenv
   source myenv/bin/activate
   ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Start the web application:
   ```bash
   sed -i 's/\r$//' start-app.sh
   bash start-app.sh
   ```

6. Open your web browser and navigate to `http://server_ip:8000`.

### Explanation

1. **Install necessary packages:** Update the package list and install `git`, `screen`, and `python3-venv` to set up the environment.

2. **Clone the repository:** Clone the File-Manager repository from GitHub and navigate into the project directory.

3. **Set up a virtual environment:** Create and activate a Python virtual environment named `myenv` to isolate project dependencies.

4. **Install dependencies:** Use pip to install all necessary Python packages listed in the `requirements.txt` file.

5. **Start the web application:** Prepare the `start-app.sh` script to run without carriage return characters and execute it to start the File-Manager web application locally.

6. **Access the application:** Open a web browser and go to `http://server_ip:8000` to use the File-Manager application.
