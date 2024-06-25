# Service Monitoring Script

This Python script uses Tkinter and Paramiko to monitor and manage services on multiple remote hosts via SSH. It allows adding hosts and services dynamically, checks service statuses, and provides an interface to restart services if needed. The GUI displays real-time status updates and logs activities for easy monitoring.

## Features

- **Service Monitoring**: Monitor the status of specified services (e.g., MySQL) on multiple hosts.
- **SSH Connectivity**: Establish SSH connections to remote hosts for executing commands.
- **Dynamic Configuration**: Easily add new hosts and services through the GUI.
- **Auto Refresh**: Automatically refresh the status of services on each host.
- **Logging**: View logs of service status checks and actions taken.

## Installation

### Prerequisites

- Python 3.x
- `paramiko` library for SSH connections
- `tkinter` library for the GUI
- `Pyinstaller` library for generate the .exe

### Install Required Libraries

```sh
> pip install paramiko tk
> pip install pyinstaller --user 
```
## Usage

1. **Setup**:
   - Ensure `hosts.json` and `services.json` files are present in the same directory as the script. These files store host credentials and services to monitor, respectively.
   - Populate `hosts.json` with host details in the format:
     ```json
     [
       {
         "code": "host_code",
         "hostname": "hostname_or_ip",
         "username": "ssh_username",
         "password": "ssh_password"
       }
     ]
     ```
   - Populate `services.json` with an array of service names to monitor.

2. **Running the Script**:
   - Execute the script 
     ```sh
       > python service_monitor.py
     ``` 
     to launch the GUI.
   - The GUI consists of two tabs: **Monitor Services** and **Add Hosts and Services**.

3. **Monitor Services Tab**:
   - Displays host status and service availability.
   - Allows refreshing status and reconnecting services.

4. **Add Hosts and Services Tab**:
   - Facilitates adding new hosts and services dynamically.

## Build

To build an executable (`service_monitor.exe`) using PyInstaller, use the following command in your terminal:

```bash
pyinstaller --onefile --add-data "hosts.json;." --add-data "services.json;." --windowed --clean -- icon=iconfinder-server2-4417099_116631.ico service_monitor.py
```


## Notes

- **SSH Connectivity**: Ensure the script can connect to the specified hosts via SSH. Verify SSH keys or password access as required.
- **Error Handling**: The script includes basic error handling for SSH connections and service checks.
- **Threading**: Uses threading to manage multiple host checks concurrently within the GUI.

## Troubleshooting

- If hosts or services are not loading correctly, ensure:
  - `hosts.json` and `services.json` files are correctly formatted and located.
  - Python environment has necessary permissions and dependencies installed.

## Contributions

### Contributions and improvements are welcome. Please fork the repository and submit pull requests.
