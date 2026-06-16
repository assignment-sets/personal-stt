#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description="Onboarding and Setup Script for PersonalSTT")
    parser.add_argument(
        "--api-key",
        help="Groq API Key to configure. If omitted, you will be prompted interactively."
    )
    return parser.parse_args()

def check_system():
    print("=== Step 1: System Checks ===")
    
    # Check OS is Linux
    if sys.platform != "linux":
        print("Error: PersonalSTT is designed to run exclusively on Linux (Ubuntu).")
        sys.exit(1)
    print("✓ Platform: Linux")
    
    # Check session server is X11
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    display = os.environ.get("DISPLAY", "")
    
    if session_type != "x11" and not display:
        print("Warning: No active X11 display detected.")
        print("PersonalSTT simulates keyboard pasting using X11 protocols.")
        print("We will proceed with installation, but ensure you run the daemon in a graphical desktop session.")
    else:
        print("✓ Display Server: X11 compatible")

def install_system_dependencies():
    print("\n=== Step 2: System Dependencies ===")
    
    dependencies = ["ffmpeg", "arecord", "aplay", "notify-send", "xclip"]
    missing = [dep for dep in dependencies if shutil.which(dep) is None]
    
    if not missing:
        print("✓ All system dependencies are present (ffmpeg, arecord, aplay, notify-send, xclip).")
        return
        
    print(f"Missing system packages: {', '.join(missing)}")
    if shutil.which("apt-get") is None:
        print("Error: apt-get not found. Please install the missing dependencies manually.")
        sys.exit(1)
        
    # Map binary names to Ubuntu apt packages
    package_map = {
        "ffmpeg": "ffmpeg",
        "arecord": "alsa-utils",
        "aplay": "alsa-utils",
        "notify-send": "libnotify-bin",
        "xclip": "xclip"
    }
    
    packages_to_install = list(set(package_map[dep] for dep in missing))
    print(f"Installing package(s) via apt: {', '.join(packages_to_install)}")
    print("This requires root permissions. Sudo prompt will appear:")
    
    try:
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y"] + packages_to_install, check=True)
        print("✓ System dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\nError: Failed to install packages: {e}")
        print(f"Please install them manually using: sudo apt install {' '.join(packages_to_install)}")
        sys.exit(1)

def sync_python_environment(project_root):
    print("\n=== Step 3: Python Environment ===")
    if shutil.which("uv") is None:
        print("Error: 'uv' executable not found in PATH.")
        print("Please install 'uv' before running this script (e.g. curl -LsSf https://astral.sh/uv/install.sh | sh)")
        sys.exit(1)
        
    print("Running 'uv sync' to build the virtual environment...")
    try:
        subprocess.run(["uv", "sync"], cwd=project_root, check=True)
        print("✓ Virtual environment synchronized.")
    except subprocess.CalledProcessError as e:
        print(f"Error: 'uv sync' failed: {e}")
        sys.exit(1)

def configure_api_key(project_root, provided_key):
    print("\n=== Step 4: Groq API Configuration ===")
    api_key = provided_key
    
    if not api_key:
        print("Find your Groq API keys at: https://console.groq.com/keys")
        api_key = input("Enter your Groq API Key: ").strip()
        while not api_key:
            api_key = input("API Key cannot be empty. Please enter your key: ").strip()
            
    env_path = os.path.join(project_root, ".env")
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f'GROQ_CONF="{api_key}"\n')
        print(f"✓ Environment variables written to: {env_path}")
    except Exception as e:
        print(f"Error: Failed to write .env file: {e}")
        sys.exit(1)

def register_daemon_service(project_root):
    print("\n=== Step 5: Daemon Service Registration ===")
    python_bin = os.path.join(project_root, ".venv", "bin", "python")
    main_py = os.path.join(project_root, "main.py")
    
    if not os.path.exists(python_bin) or not os.path.exists(main_py):
        print("Error: Could not locate virtualenv python or main.py. Did 'uv sync' fail?")
        sys.exit(1)
        
    try:
        subprocess.run([python_bin, main_py, "install"], check=True)
        print("✓ Background systemd service registered and activated!")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to register systemd service: {e}")
        sys.exit(1)

def print_post_install_guide(project_root):
    python_bin = os.path.join(project_root, ".venv", "bin", "python")
    main_py = os.path.join(project_root, "main.py")
    
    print("\n" + "="*50)
    print("           🎉 PersonalSTT SETUP COMPLETE! 🎉")
    print("="*50)
    print("\nTo finish setting up global control, map the following Custom")
    print("Keyboard Shortcuts in: Settings ➔ Keyboard ➔ Keyboard Shortcuts ➔ Custom Shortcuts")
    print("\n1. START RECORDING")
    print("   Name:      PersonalSTT - Start")
    print(f"   Command:   {python_bin} {main_py} start")
    print("   Shortcut:  Ctrl+Shift+D")
    print("\n2. STOP & INSERT TEXT")
    print("   Name:      PersonalSTT - Stop")
    print(f"   Command:   {python_bin} {main_py} stop")
    print("   Shortcut:  Ctrl+Shift+S")
    print("\n3. CANCEL RECORDING")
    print("   Name:      PersonalSTT - Cancel")
    print(f"   Command:   {python_bin} {main_py} cancel")
    print("   Shortcut:  Ctrl+Shift+Q")
    
    print("\n" + "-"*50)
    print("💡 Command Line Shortcut (Recommended):")
    print("Add an alias to easily interact via terminal by running this command once:")
    print(f'echo \'alias pstt="{python_bin} {main_py}"\' >> ~/.bashrc && source ~/.bashrc')
    print("\nThen run 'pstt status' to verify everything is working!")
    print("="*50 + "\n")

def main():
    args = parse_args()
    
    # Resolve project root (one level above this script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    check_system()
    install_system_dependencies()
    sync_python_environment(project_root)
    configure_api_key(project_root, args.api_key)
    register_daemon_service(project_root)
    print_post_install_guide(project_root)

if __name__ == "__main__":
    main()
