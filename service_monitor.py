import sys
import os
import paramiko
import tkinter as tk
from tkinter import messagebox, scrolledtext, font
from tkinter import ttk
import threading
import json

HOSTS_FILE = "hosts.json"
SERVICES_FILE = "services.json"


# Determine the path to the JSON files based on whether the script is frozen or not
if getattr(sys, 'frozen', False):
    # If the script is run as a bundled executable
    base_path = sys._MEIPASS  # PyInstaller stores the bundled data in this attribute
else:
    # If the script is run as a regular Python script
    base_path = os.path.abspath(os.path.dirname(__file__))

HOSTS_FILE = os.path.join(base_path, "hosts.json")
SERVICES_FILE = os.path.join(base_path, "services.json")

try:
    with open(HOSTS_FILE, 'r') as f:
        hosts = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    hosts = []
    print(f"Error loading {HOSTS_FILE}: {e}")

try:
    with open(SERVICES_FILE, 'r') as f:
        services = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    services = []
    print(f"Error loading {SERVICES_FILE}: {e}")


try:
    with open(HOSTS_FILE, 'r') as f:
        hosts = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    hosts = []
    print(f"Error loading {HOSTS_FILE}: {e}")

try:
    with open(SERVICES_FILE, 'r') as f:
        services = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    services = []
    print(f"Error loading {SERVICES_FILE}: {e}")

def ssh_command(host, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host["hostname"], username=host["username"], password=host["password"])
        stdin, stdout, stderr = client.exec_command(command)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except paramiko.ssh_exception.NoValidConnectionsError:
        return "", "SSH connection failed"
    except Exception as e:
        return "", str(e)
    finally:
        client.close()

def check_host_reachability(host):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host["hostname"], username=host["username"], password=host["password"])
        client.close()
        return True, ""
    except paramiko.ssh_exception.NoValidConnectionsError:
        return False, "SSH connection failed"
    except Exception as e:
        return False, str(e)

def check_mysql_status(host):
    output, error = ssh_command(host, "service mysqld status")
    if "Active: active (running)" in output:
        return True, output, ""
    else:
        return False, output, error

def check_service_status(host, service):
    if service == "mysql":
        return check_mysql_status(host)
    else:
        output, error = ssh_command(host, f"systemctl is-active {service}")
        return output == "active", output, error

def start_service(host, service):
    output, error = ssh_command(host, f"sudo systemctl start {service}")
    return output, error

class ServiceMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Service Monitor")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=1, fill="both")

        self.monitor_frame = tk.Frame(self.notebook)
        self.add_host_frame = tk.Frame(self.notebook)

        self.notebook.add(self.monitor_frame, text="Monitor Services")
        self.notebook.add(self.add_host_frame, text="Add Hosts and Services")

        self.create_monitor_ui()
        self.create_add_host_ui()

    def create_monitor_ui(self):
        self.canvas = tk.Canvas(self.monitor_frame)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollbar = ttk.Scrollbar(self.monitor_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

        header_font = font.Font(family="Helvetica", size=12, weight="bold")
        status_font = font.Font(family="Comic Sans MS", size=10, weight="normal")

        headers = ["Hosts"] + services + ["Action"]
        for col, header in enumerate(headers):
            tk.Label(self.scrollable_frame, text=header, font=header_font, fg="red").grid(row=0, column=col, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(self.scrollable_frame, wrap=tk.WORD, height=10)
        self.log_text.grid(row=len(hosts) + 2, column=0, columnspan=len(services) + 2, padx=10, pady=10, sticky="nsew")

        self.status_labels = {}
        self.host_labels = {}
        self.reconnect_buttons = {}

        for row, host in enumerate(hosts, start=1):
            host_label = tk.Label(self.scrollable_frame, text=host["code"], font=status_font)
            host_label.grid(row=row, column=0, padx=10, pady=5)
            self.host_labels[row] = host_label

            for col, service in enumerate(services, start=1):
                label = tk.Label(self.scrollable_frame, text="Checking...", font=status_font)
                label.grid(row=row, column=col, padx=10, pady=5)
                self.status_labels[(row, col)] = label

            refresh_button = tk.Button(self.scrollable_frame, text="Refresh", command=lambda h=host, r=row: self.refresh_host_services(h, r))
            refresh_button.grid(row=row, column=len(services) + 1, padx=10, pady=5)
            self.reconnect_buttons[(row, len(services) + 1)] = refresh_button

            threading.Thread(target=self.update_status, args=(host, row)).start()

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def refresh_host_services(self, host, row):
        for col, service in enumerate(services, start=1):
            status_label = self.status_labels[(row, col)]
            status_label.config(text="Checking...")
            status, output, error = check_service_status(host, service)
            if status:
                status_label.config(text="Available", fg="green")
            else:
                reconnect_command = f"sudo systemctl restart {service}" if service != "mysql" else "service mysqld restart"
                reconnect_button = tk.Button(self.scrollable_frame, text="Reconnect", command=lambda h=host, s=service, cmd=reconnect_command: self.reconnect_service(h, s, cmd))
                reconnect_button.grid(row=row, column=col, padx=10, pady=5)
                self.reconnect_buttons[(row, col)] = reconnect_button
                status_label.config(text="Not working", fg="red")
            self.log_text.insert(tk.END, f"Checked {service} on {host['hostname']}: {output or error}\n")
            self.log_text.see(tk.END)

    def update_status(self, host, row):
        is_reachable, error = check_host_reachability(host)
        host_label = self.host_labels[row]
        if not is_reachable:
            host_label.config(fg="red")
            self.log_text.insert(tk.END, f"Host {host['hostname']} is unreachable: {error}\n")
            self.log_text.see(tk.END)
            for col, service in enumerate(services, start=1):
                label = tk.Label(self.scrollable_frame, text="Not working", fg="red", font=font.Font(family="Comic Sans MS", size=10, weight="normal"))
                label.grid(row=row, column=col, padx=10, pady=5)
                self.status_labels[(row, col)] = label
            return

        host_label.config(fg="black")
        for col, service in enumerate(services, start=1):
            status, output, error = check_service_status(host, service)
            label = self.status_labels[(row, col)]
            if status:
                label.config(text="Available", fg="green")
            else:
                reconnect_command = f"sudo systemctl restart {service}" if service != "mysql" else "service mysqld restart"
                reconnect_button = tk.Button(self.scrollable_frame, text="Reconnect", command=lambda h=host, s=service, cmd=reconnect_command: self.reconnect_service(h, s, cmd))
                reconnect_button.grid(row=row, column=col, padx=10, pady=5)
                self.reconnect_buttons[(row, col)] = reconnect_button
                label.config(text="Not working", fg="red")
            self.log_text.insert(tk.END, f"Checked {service} on {host['hostname']}: {output or error}\n")
            self.log_text.see(tk.END)

    def reconnect_service(self, host, service, command):
        output, error = ssh_command(host, command)
        status, _, _ = check_service_status(host, service)
        for (row, col), button in self.reconnect_buttons.items():
            if button.cget('text') == 'Reconnect':
                button.grid_forget()
        self.refresh_status()

    def refresh_status(self):
        for row, host in enumerate(hosts, start=1):
            threading.Thread(target=self.update_status, args=(host, row)).start()

    def create_add_host_ui(self):
        add_host_frame = tk.LabelFrame(self.add_host_frame, text="Add Host", padx=10, pady=10)
        add_host_frame.grid(row=0, column=0, padx=20, pady=20)

        tk.Label(add_host_frame, text="Host Code:").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(add_host_frame, text="Hostname:").grid(row=1, column=0, padx=10, pady=5)
        tk.Label(add_host_frame, text="Username:").grid(row=2, column=0, padx=10, pady=5)
        tk.Label(add_host_frame, text="Password:").grid(row=3, column=0, padx=10, pady=5)

        self.host_code_entry = tk.Entry(add_host_frame)
        self.hostname_entry = tk.Entry(add_host_frame)
        self.username_entry = tk.Entry(add_host_frame)
        self.password_entry = tk.Entry(add_host_frame, show="*")

        self.host_code_entry.grid(row=0, column=1, padx=10, pady=5)
        self.hostname_entry.grid(row=1, column=1, padx=10, pady=5)
        self.username_entry.grid(row=2, column=1, padx=10, pady=5)
        self.password_entry.grid(row=3, column=1, padx=10, pady=5)

        self.add_host_button = tk.Button(add_host_frame, text="Add Host", command=self.add_host)
        self.add_host_button.grid(row=4, column=0, columnspan=2, pady=10)

        add_service_frame = tk.LabelFrame(self.add_host_frame, text="Add Service", padx=10, pady=10)
        add_service_frame.grid(row=1, column=0, padx=20, pady=20)

        tk.Label(add_service_frame, text="Service Name:").grid(row=0, column=0, padx=10, pady=5)

        self.service_name_entry = tk.Entry(add_service_frame)
        self.service_name_entry.grid(row=0, column=1, padx=10, pady=5)

        self.add_service_button = tk.Button(add_service_frame, text="Add Service", command=self.add_service)
        self.add_service_button.grid(row=1, column=0, columnspan=2, pady=10)

    def add_host(self):
        new_host = {
            "code": self.host_code_entry.get(),
            "hostname": self.hostname_entry.get(),
            "username": self.username_entry.get(),
            "password": self.password_entry.get()
        }
        hosts.append(new_host)
        with open(HOSTS_FILE, 'w') as f:
            json.dump(hosts, f)
        messagebox.showinfo("Success", "Host added successfully!")
        self.host_code_entry.delete(0, tk.END)
        self.hostname_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.refresh_monitor_tab()

    def add_service(self):
        new_service = self.service_name_entry.get()
        if new_service and new_service not in services:
            services.append(new_service)
            with open(SERVICES_FILE, 'w') as f:
                json.dump(services, f)
            messagebox.showinfo("Success", "Service added successfully!")
            self.service_name_entry.delete(0, tk.END)
            self.refresh_monitor_tab()

    def refresh_monitor_tab(self):
        self.notebook.forget(self.monitor_frame)
        self.monitor_frame = tk.Frame(self.notebook)
        self.notebook.insert(0, self.monitor_frame, text="Monitor Services")
        self.create_monitor_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServiceMonitorApp(root)
    root.mainloop()
