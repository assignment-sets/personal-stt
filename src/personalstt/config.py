import os
import json

def load_env(base_dir):
    """Parses a local .env file in the project folder to populate environment variables."""
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API Configurations
def get_api_key():
    load_env(PROJECT_ROOT)
    return os.environ.get("GROQ_CONF") or os.environ.get("GROQ_API_KEY")

# IPC & File Path Configurations
SOCKET_PATH = "/tmp/personalstt.socket"
TEMP_WAV_PATH = "/tmp/personalstt_recording.wav"
SOUND_DIR = os.path.expanduser("~/.local/share/personalstt/sounds")

# Config File Configurations
CONFIG_DIR = os.path.expanduser("~/.config/personalstt")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "max_duration_sec": 240,
    "groq_model": "whisper-large-v3-turbo",
    "api_retries": 3,
    "alsa_device": "default",
    "feedback_volume": 0.3,
    "notify_timeout_ms": 2000
}

CONFIG_DESCRIPTIONS = {
    "max_duration_sec": "Hard recording timeout in seconds (auto-cancels recording after this)",
    "groq_model": "The Groq STT model used for transcribing",
    "api_retries": "Number of times to retry Groq API requests on connection failure",
    "alsa_device": "The ALSA recording input device name (passed to arecord -D)",
    "feedback_volume": "Volume level (0.0 to 1.0) of the synthesized audio beeps",
    "notify_timeout_ms": "Desktop notification duration in milliseconds"
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
        
        # Range checks for positive numbers
        if key in ("max_duration_sec", "api_retries", "notify_timeout_ms") and casted_value <= 0:
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
