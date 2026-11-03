import os
import json

# IPC & File Path Configurations
SOCKET_PATH = "/tmp/personalstt.socket"
TEMP_WAV_PATH = "/tmp/personalstt_recording.wav"
SOUND_DIR = os.path.expanduser("~/.local/share/personalstt/sounds")

# Config & Credential File Configurations
CONFIG_DIR = os.path.expanduser("~/.config/personalstt")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials")


def ensure_secure_permissions(filepath, expected_mode=0o600):
    """
    Checks that the file does not have loose permissions (group/world accessible).
    If it does, automatically restricts it to expected_mode (default: 0600) and prints a warning.
    """
    try:
        current_mode = os.stat(filepath).st_mode & 0o777
        # Check if group or other has any permissions (read, write, or execute)
        if current_mode & 0o077 != 0:
            print(f"Security Notice: File '{filepath}' had loose permissions ({oct(current_mode)}). Restricting to {oct(expected_mode)}.")
            os.chmod(filepath, expected_mode)
    except Exception as e:
        print(f"Warning: Could not check or enforce secure permissions on '{filepath}': {e}")


def secure_write_credentials(api_key, path=CREDENTIALS_FILE):
    """
    Atomically writes the API key into a dedicated credentials file with strict 0600 permissions
    inside an isolated directory with 0700 permissions.
    """
    dir_path = os.path.dirname(os.path.abspath(path))
    os.makedirs(dir_path, mode=0o700, exist_ok=True)
    # Ensure directory permissions are 0700 even if directory already existed
    try:
        if (os.stat(dir_path).st_mode & 0o777) != 0o700:
            os.chmod(dir_path, 0o700)
    except Exception:
        pass

    content = f'GROQ_CONF="{api_key}"\n'
    # Use low-level open with O_CREAT | O_WRONLY | O_TRUNC and mode 0600
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as f:
            f.write(content)
        # Explicit chmod call to guarantee permissions regardless of umask
        os.chmod(path, 0o600)
        return True
    except Exception as e:
        print(f"Error securely writing credentials: {e}")
        return False


def parse_key_value_file(filepath):
    """Parses key=value lines from a file and returns a dictionary."""
    data = {}
    if os.path.exists(filepath):
        ensure_secure_permissions(filepath, expected_mode=0o600)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, val = line.split("=", 1)
                            data[key.strip()] = val.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Warning: Could not read credentials file '{filepath}': {e}")
    return data


def load_env(base_dir):
    """Parses a local .env file in the project folder to populate environment variables."""
    env_path = os.path.join(base_dir, ".env")
    env_data = parse_key_value_file(env_path)
    for key, val in env_data.items():
        os.environ[key] = val


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# API Configurations
def get_api_key():
    """
    Retrieves the Groq API key according to priority:
    1. Environment variables GROQ_CONF or GROQ_API_KEY
    2. Secure user credentials file: ~/.config/personalstt/credentials
    3. Legacy project root .env file
    """
    key = os.environ.get("GROQ_CONF") or os.environ.get("GROQ_API_KEY")
    if key:
        return key

    # Check ~/.config/personalstt/credentials
    if os.path.exists(CREDENTIALS_FILE):
        creds = parse_key_value_file(CREDENTIALS_FILE)
        key = creds.get("GROQ_CONF") or creds.get("GROQ_API_KEY")
        if key:
            return key

    # Check legacy .env in project root
    load_env(PROJECT_ROOT)
    return os.environ.get("GROQ_CONF") or os.environ.get("GROQ_API_KEY")

DEFAULT_CONFIG = {
    "max_duration_sec": 300,
    "groq_model": "whisper-large-v3-turbo",
    "api_retries": 3,
    "alsa_device": "default",
    "feedback_volume": 0.3,
    "feedback_mode": "both",
    "notify_timeout_ms": 2000,
    "auto_dismiss_ms": 1200,
    "language": "en",
    "prompt": "",
    "auto_paste": True
}

CONFIG_DESCRIPTIONS = {
    "max_duration_sec": "Hard recording timeout in seconds (auto-cancels recording after this)",
    "groq_model": "The Groq STT model used for transcribing",
    "api_retries": "Number of times to retry Groq API requests on connection failure",
    "alsa_device": "The ALSA recording input device name (passed to arecord -D)",
    "feedback_volume": "Volume level (0.0 to 1.0) of the synthesized audio beeps",
    "feedback_mode": "Feedback style: 'both' (audio & visual), 'audio_only', 'visual_only', or 'errors_only'",
    "notify_timeout_ms": "Desktop notification duration in milliseconds",
    "auto_dismiss_ms": "Duration in ms before 'Speech inserted!' notification auto-dismisses",
    "language": "Spoken audio language code (e.g. 'en', 'es', or empty for auto-detect)",
    "prompt": "Optional vocabulary hint or phrasing guidance passed to Groq Whisper",
    "auto_paste": "Automatically simulate Ctrl+V to paste transcribed text (true/false)"
}

def load_config():
    """Loads settings from the JSON config file, creating it with defaults if missing."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge loaded keys into defaults to ensure new keys are populated
                for k, v in loaded.items():
                    if k in DEFAULT_CONFIG:
                        # Cast to correct type
                        expected_type = type(DEFAULT_CONFIG[k])
                        try:
                            config[k] = expected_type(v)
                        except (ValueError, TypeError):
                            print(f"Warning: Config key '{k}' has invalid value type. Resetting to default.")
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}. Using defaults.")
            
    # Always write back to ensure the file exists and is well-formatted
    save_config(config)
    return config

def save_config(config):
    """Saves config dictionary to config file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config file: {e}")
        return False

def set_config_value(key, value):
    """Sets a configuration value, parsing/validating the type. Returns (success, error_msg)."""
    if key not in DEFAULT_CONFIG:
        return False, f"Unknown configuration key: {key}"
        
    config = load_config()
    expected_type = type(DEFAULT_CONFIG[key])
    
    try:
        # Special parsing for bool if needed (none currently, but good practice)
        if expected_type is bool:
            if str(value).lower() in ("true", "1", "yes"):
                casted_value = True
            elif str(value).lower() in ("false", "0", "no"):
                casted_value = False
            else:
                raise ValueError("Value must be a boolean.")
        else:
            casted_value = expected_type(value)
            
        # Range checks for volume
        if key == "feedback_volume" and not (0.0 <= casted_value <= 1.0):
            return False, "feedback_volume must be between 0.0 and 1.0"
        
        # Validation for feedback_mode
        if key == "feedback_mode" and casted_value not in ("both", "audio_only", "visual_only", "errors_only"):
            return False, "feedback_mode must be one of: 'both', 'audio_only', 'visual_only', 'errors_only'"

        # Range checks for positive numbers
        if key in ("max_duration_sec", "api_retries", "notify_timeout_ms", "auto_dismiss_ms") and casted_value <= 0:
            return False, f"{key} must be a positive number greater than 0"
            
        config[key] = casted_value
        save_config(config)
        
        # If feedback volume changed, delete wave files so sound engine regenerates them on next play
        if key == "feedback_volume":
            for name in ("start.wav", "stop.wav", "success.wav", "error.wav"):
                wav_path = os.path.join(SOUND_DIR, name)
                if os.path.exists(wav_path):
                    try:
                        os.remove(wav_path)
                    except Exception:
                        pass
                        
        return True, ""
    except (ValueError, TypeError) as e:
        return False, f"Invalid value type. Expected {expected_type.__name__}: {e}"
