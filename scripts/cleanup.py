#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def check_system():
    if sys.platform != "linux":
        print("Error: This script is designed for Linux (Ubuntu).")
        sys.exit(1)

def stop_and_remove_systemd_service():
    print("=== Step 1: Removing systemd User Service ===")
    
    # 1. Stop and disable systemd service
    try:
        print("Stopping and disabling personalstt.service...")
        subprocess.run(["systemctl", "--user", "disable", "--now", "personalstt.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception as e:
        print(f"Warning: Failed to stop service: {e}")
        
    # 2. Delete service file
    service_path = os.path.expanduser("~/.config/systemd/user/personalstt.service")
    if os.path.exists(service_path):
        try:
            os.remove(service_path)
            print(f"Removed systemd unit file: {service_path}")
        except Exception as e:
            print(f"Error: Failed to delete service file: {e}")
    else:
        print("Systemd unit file not found (already removed).")
        
    # 3. Reload daemon
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    except Exception:
        pass
    print("✓ Systemd service removed.")

def remove_temp_files_and_sockets():
    print("\n=== Step 2: Purging Temp Files & Sockets ===")
    
    files_to_remove = [
        "/tmp/personalstt.socket",
        "/tmp/personalstt_recording.wav"
    ]
    
    for filepath in files_to_remove:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Removed: {filepath}")
            except Exception as e:
                print(f"Warning: Failed to delete {filepath}: {e}")
    print("✓ Temporary sockets and audio files purged.")

def remove_configurations_and_assets():
    print("\n=== Step 3: Deleting Configs & Generated Sounds ===")
    
    dirs_to_remove = [
        os.path.expanduser("~/.config/personalstt"),          # config.json
        os.path.expanduser("~/.local/share/personalstt")     # Synthesized sounds
    ]
    
    for dirpath in dirs_to_remove:
        if os.path.exists(dirpath):
            try:
                shutil.rmtree(dirpath)
                print(f"Deleted directory: {dirpath}")
            except Exception as e:
                print(f"Warning: Failed to remove directory {dirpath}: {e}")
        else:
            print(f"Directory not found (already deleted): {dirpath}")
    print("✓ Local configurations and sound assets deleted.")

def remove_credentials(project_root):
    print("\n=== Step 4: Deleting Credentials ===")
    
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        try:
            os.remove(env_path)
            print(f"Removed environment file: {env_path}")
        except Exception as e:
            print(f"Warning: Failed to remove {env_path}: {e}")
    else:
        print("No .env credentials file found.")
    print("✓ API credential file removed.")

def print_manual_cleanup_guide(project_root):
    print("\n" + "="*50)
    print("        🧹 PersonalSTT CLEANUP COMPLETE! 🧹")
    print("="*50)
    print("\nTo complete the offboarding, please perform these manual steps:")
    
    print("\n1. REMOVE KEYBOARD SHORTCUTS")
    print("   Go to Settings ➔ Keyboard ➔ Custom Shortcuts, and remove:")
    print("   - 'PersonalSTT - Start'")
    print("   - 'PersonalSTT - Stop'")
    print("   - 'PersonalSTT - Cancel'")
    
    print("\n2. REMOVE SHELL ALIAS")
    print("   Open your ~/.bashrc file in an editor, delete the following line,")
    print("   and reload your terminal (source ~/.bashrc):")
    print("   alias pstt=\"...\"")
    
    print("\n3. UNINSTALL SYSTEM DEPENDENCIES (Optional)")
    print("   If you do not use them for other apps, you can remove them via apt:")
    print("   sudo apt remove alsa-utils libnotify-bin xclip ffmpeg")
    
    print("\n4. DELETE REPOSITORY FOLDER")
    print("   You can now safely delete the project files:")
    print(f"   rm -rf {project_root}")
    print("="*50 + "\n")

def main():
    check_system()
    
    # Resolve project root (one level above this script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Run cleanup steps
    stop_and_remove_systemd_service()
    remove_temp_files_and_sockets()
    remove_configurations_and_assets()
    remove_credentials(project_root)
    print_manual_cleanup_guide(project_root)

if __name__ == "__main__":
    main()
