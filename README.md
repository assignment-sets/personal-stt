# PersonalSTT

PersonalSTT is a dead-simple, ultra-lightweight background Speech-to-Text (STT) utility designed specifically for Ubuntu (X11). It interfaces with the Groq Whisper API (`whisper-large-v3-turbo`) to transcribe your voice on-the-fly and instantly paste it at your active cursor.

---

## Key Features

- **Systemd User Service:** Runs seamlessly in the background as a daemon. It starts automatically when you log into your desktop.
- **Zero GUI, Zero Clutter:** No windows, taskbars, or menus. Control everything globally using system keyboard shortcuts.
- **Hardware Audio Feedback:** Generates instant audio beep cues (rising chime for start, falling chirp for stop, double-beep for success, warning buzz for errors) using ALSA's `aplay`.
- **Dynamic Configurations:** Customize ALSA recording devices, volumes, timeouts, and safety limits on-the-fly via the CLI.
- **Safety Lockouts:** Automatically cancels recording after a configured duration (defaults to 4 minutes) to prevent accidental open microphones or API quota drainage.
- **Clipboard-based Error Debugging:** If the API fails due to rate limits, quota issues, or auth issues, the daemon copies the full raw error message to your clipboard and shows a persistent system notification. Just press `Ctrl+V` anywhere to see the exact issue.

---

## Onboarding (Installation)

### 1. Clone the Repository

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/yourusername/personalSTT.git
cd personalSTT
```

### 2. Run the Onboarding Script

Give executive permissions to the scripts and run the setup utility:

```bash
chmod +x scripts/*.py
./scripts/setup.py
```

#### What the Onboarding Script Does:

- Verifies that your environment runs under Linux/X11.
- Checks for and installs missing system dependencies via `apt-get` (`ffmpeg`, `alsa-utils`, `libnotify-bin`, `xclip`).
- Configures your python virtual environment using `uv sync`.
- Prompts you for your Groq API Key and writes it to a local `.env` file.
- Registers and starts the systemd user daemon.
- Prints out exact copy-paste instructions to map global keyboard shortcuts in Ubuntu.

---

## CLI Commands Reference

All interactions with the background daemon can be done via the CLI. If you set up the suggested alias `pstt` during onboarding, you can run:

- **`pstt start`**: Starts voice recording.
- **`pstt stop`**: Stops recording, submits audio to Groq Whisper, and pastes transcription at the cursor.
- **`pstt cancel`**: Cancels any current recording or transcription session.
- **`pstt status`**: Prints diagnostic details about the daemon and the systemd service.
- **`pstt restart`**: Restarts the background systemd user service.
- **`pstt config list`**: Lists all configurable settings, current values, and descriptions.
- **`pstt config set <key> <value>`**: Sets a configuration key to a new value.
- **`pstt config get <key>`**: Returns the current value of a configuration key.

---

## Configuration Settings Reference

Configurations are stored in `~/.config/personalstt/config.json`. You can modify them directly or using `pstt config set <key> <value>`:

| Setting Key         | Default Value              | Type    | Description                                                                                                |
| :------------------ | :------------------------- | :------ | :--------------------------------------------------------------------------------------------------------- |
| `max_duration_sec`  | `240`                      | `int`   | Safety duration limit in seconds. Recording auto-cancels if it exceeds this threshold.                     |
| `groq_model`        | `"whisper-large-v3-turbo"` | `str`   | Groq Whisper model used for STT inference.                                                                 |
| `feedback_volume`   | `0.3`                      | `float` | Volume (`0.0` to `1.0`) of the feedback sound beeps. Changing this automatically regenerates sound assets. |
| `alsa_device`       | `"default"`                | `str`   | ALSA recording microphone input device name (passed to `arecord -D`).                                      |
| `api_retries`       | `3`                        | `int`   | Number of times to retry Groq API connections on failures.                                                 |
| `notify_timeout_ms` | `2000`                     | `int`   | Duration (in milliseconds) that desktop notifications stay on-screen.                                      |

---

## Offboarding (Cleanup & Uninstallation)

If you ever want to completely remove the utility from your system, run the cleanup script:

```bash
./scripts/cleanup.py
```

#### What the Cleanup Script Does:

- Disables and stops the systemd background service.
- Deletes the service unit file and reloads systemd.
- Deletes the temporary socket file and audio recordings.
- Purges local configurations (`~/.config/personalstt/`) and synthesized WAV assets (`~/.local/share/personalstt/`).
- Deletes your local API credentials (`.env`).
- Displays guidance on removing the mapped keyboard shortcuts, shell alias, and apt dependencies from your system.
