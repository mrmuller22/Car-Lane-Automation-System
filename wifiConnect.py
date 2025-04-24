import subprocess
import time
import os

# Variable of path to Kiosk Program
APP_PATH = "/home/admin/Desktop/Senior\ Project/main.py" 


def is_connected():
    # Function that check if wifi is connected

    try:
        result = subprocess.check_output(["iwgetid"])
        return bool(result.strip())
    except subprocess.CalledProcessError:
        return False

def auto_connect():
    # Function that auto connects each saved network

    try:
        print("Trying auto-connect to known networks...")
        subprocess.run(["nmcli", "networking", "on"], check=True)
        subprocess.run(["nmcli", "device", "wifi", "rescan"], check=True)

        # List saved connections and try to bring them up
        saved = subprocess.check_output(["nmcli", "-t", "-f", "NAME", "connection", "show"]).decode().splitlines()

        for conn in saved:
            print(f"Trying saved network: {conn}")
            try:
                subprocess.run(["nmcli", "connection", "up", conn], check=True)
                if is_connected():
                    print(f"Connected to {conn}")
                    return True
            except subprocess.CalledProcessError:
                print(f"Failed to connect to {conn}")
                continue
        return False
    except subprocess.CalledProcessError:
        return False

def list_wifi_networks():
    # Function that list read wifi networks

    try:
        networks = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "device", "wifi", "list"])
        ssids = list(filter(None, networks.decode().split('\n')))
        return list(dict.fromkeys(ssids))
    except subprocess.CalledProcessError:
        return []

def connect_to_wifi(ssid, password=None):
    # Function that connects to wifi

    try:
        # Check for existing saved profile
        saved = subprocess.check_output(["nmcli", "-t", "-f", "NAME", "connection", "show"]).decode().splitlines()

        if ssid in saved:
            print(f"Using saved profile for {ssid}")
            subprocess.run(["nmcli", "connection", "up", ssid], check=True)
        else:
            print(f"Connecting to {ssid} and saving credentials...")
            subprocess.run(["nmcli", "device", "wifi", "connect", ssid, "password", password], check=True)

        return is_connected()
    except subprocess.CalledProcessError as e:
        print(f"Failed to connect to {ssid}: {e}")
        return False

def prompt_user_for_connection():
    # Function to prompt user for wifi credentials

    print("Scanning for available networks...\n")
    ssids = list_wifi_networks()

    if not ssids:
        print("No networks found.")
        return False

    for idx, ssid in enumerate(ssids):
        print(f"{idx + 1}: {ssid}")

    try:
        choice = int(input("\nSelect a network (number): ")) - 1
        ssid = ssids[choice]

        # Check if it's already saved
        saved = subprocess.check_output(["nmcli", "-t", "-f", "NAME", "connection", "show"]).decode().splitlines()
        if ssid in saved:
            print(f"{ssid} already saved. Connecting...")
            return connect_to_wifi(ssid)
        else:
            password = input(f"Enter password for {ssid}: ")
            return connect_to_wifi(ssid, password)
    except (IndexError, ValueError):
        print("Invalid selection.")
        return False

def launch_gui_app():
    # Function to launch Kiosk Program
    
    print("Launching GUI app...")
    os.system(f"/home/admin/Desktop/Senior\ Project/venv/bin/python3.11 {APP_PATH}")

def main():
    print("Wi-Fi Manager Starting...")

    if is_connected():
        print("Already connected to Wi-Fi.")
    else:
        connected = auto_connect()
        if not connected:
            print("Auto-connect failed. Asking user...")
            connected = prompt_user_for_connection()

        if not connected:
            print("Still not connected. Continuing anyway...")

    time.sleep(2)
    launch_gui_app()

if __name__ == "__main__":
    main()