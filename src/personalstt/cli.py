import os
import sys
import socket
import subprocess

def send_command(command):
    """Sends a command to the Unix domain socket and prints the response."""
    from personalstt.config import SOCKET_PATH
    if not os.path.exists(SOCKET_PATH):
        print("Error: The PersonalSTT daemon socket does not exist. Is the background daemon running?")
        print("Try starting it with: systemctl --user start personalstt.service")
        return False
        
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(SOCKET_PATH)
        client.sendall(command.encode("utf-8"))
        response = client.recv(1024).decode("utf-8")
        print(f"Daemon response: {response}")
        return True
    except Exception as e:
        print(f"Failed to connect to daemon socket: {e}")
        return False
    finally:
        client.close()

def print_status():
    """Prints diagnostic information about the socket and systemd service."""
    from personalstt.config import SOCKET_PATH
    socket_running = os.path.exists(SOCKET_PATH)
    
    print("=== PersonalSTT Status ===")
    if socket_running:
        print("Daemon IPC Socket: Active")
        # Query socket state
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.connect(SOCKET_PATH)
            client.sendall(b"status")
            state = client.recv(1024).decode("utf-8")
            print(f"Daemon Current State: {state}")
        except Exception as e:
            print(f"Daemon Current State: Offline/Unreachable ({e})")
        finally:
            client.close()
    else:
        print("Daemon IPC Socket: Inactive (Offline)")
        
    print("\n=== Systemd Service Status ===")
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", "personalstt.service"],
            capture_output=True, text=True, check=False
        )
        service_active = res.stdout.strip()
        print(f"Systemd User Service: {service_active}")
        if service_active != "active":
            print("Tip: Run 'python main.py install' to set up and start the background daemon.")
    except Exception as e:
        print(f"Could not retrieve systemd status: {e}")

def restart_service():
    """Restarts the systemd user service."""
    print("Restarting systemd personalstt service...")
    try:
        subprocess.run(["systemctl", "--user", "restart", "personalstt.service"], check=True)
        print("Service restarted successfully.")
    except Exception as e:
        print(f"Failed to restart service: {e}")

def install_service():
    """Dynamically installs, enables, and starts the systemd user service."""
    # Find current python executable inside the virtualenv
    python_exe = sys.executable
    
    # Resolve the project root and main.py path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main_py_path = os.path.join(project_root, "main.py")
    
    service_content = f"""[Unit]
Description=Personal Speech to Text Daemon
After=default.target

[Service]
Type=simple
WorkingDirectory={project_root}
ExecStart={python_exe} {main_py_path} --daemon
Restart=always
RestartSec=1
Environment=DISPLAY=:0
Environment=XAUTHORITY=%t/gdm/Xauthority
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
    
    systemd_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(systemd_dir, exist_ok=True)
    service_path = os.path.join(systemd_dir, "personalstt.service")
    
    try:
        with open(service_path, "w", encoding="utf-8") as f:
            f.write(service_content)
        print(f"Service file written to {service_path}")
        
        # Systemd manager actions
        print("Running: systemctl --user daemon-reload...")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        
        print("Running: systemctl --user enable --now personalstt.service...")
        subprocess.run(["systemctl", "--user", "enable", "--now", "personalstt.service"], check=True)
        
        print("\nInstallation successful! Service details:")
        subprocess.run(["systemctl", "--user", "status", "personalstt.service"], check=False)
    except Exception as e:
        print(f"Installation failed: {e}")

def print_help():
    print("Usage: python main.py <command>")
    print("\nAvailable commands:")
    print("  start     - Start listening and recording audio")
    print("  stop      - Stop recording and trigger Groq API transcription + paste")
    print("  cancel    - Cancel recording or transcription")
    print("  status    - Print daemon state and systemd service status")
    print("  restart   - Restart the systemd background service")
    print("  install   - Register and run the daemon as a systemd user service")
    print("  config    - Manage configuration settings (list, get, set)")
    print("  --daemon  - Run the daemon socket listener directly (used by systemd)")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    
    if cmd == "--daemon":
        from personalstt.daemon import RecordingDaemon
        daemon = RecordingDaemon()
        daemon.run()
    elif cmd == "start":
        send_command("start")
    elif cmd == "stop":
        send_command("stop")
    elif cmd == "cancel":
        send_command("cancel")
    elif cmd == "status":
        print_status()
    elif cmd == "restart":
        restart_service()
    elif cmd == "install":
        install_service()
    elif cmd == "config":
        if len(sys.argv) < 3:
            print("Usage: pstt config <action> [args]")
            print("Actions: list, get <key>, set <key> <value>")
            sys.exit(1)
            
        action = sys.argv[2].lower()
        from personalstt.config import load_config, set_config_value, CONFIG_DESCRIPTIONS
        
        if action == "list":
            config = load_config()
            print("=== PersonalSTT Configuration Settings ===")
            for k, v in config.items():
                desc = CONFIG_DESCRIPTIONS.get(k, "")
                print(f"  {k:<20} = {v:<25} # {desc}")
        elif action == "get":
            if len(sys.argv) < 4:
                print("Usage: pstt config get <key>")
                sys.exit(1)
            key = sys.argv[3]
            config = load_config()
            if key in config:
                print(config[key])
            else:
                print(f"Error: Unknown configuration key '{key}'")
                sys.exit(1)
        elif action == "set":
            if len(sys.argv) < 5:
                print("Usage: pstt config set <key> <value>")
                sys.exit(1)
            key = sys.argv[3]
            value = sys.argv[4]
            success, err = set_config_value(key, value)
            if success:
                print(f"Success: Set '{key}' to '{value}'")
            else:
                print(f"Error: {err}")
                sys.exit(1)
        else:
            print(f"Error: Unknown config action '{action}'")
            print("Actions: list, get <key>, set <key> <value>")
            sys.exit(1)
    else:
        print(f"Unknown command: {cmd}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
