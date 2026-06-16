# PersonalSTT: CLI Commands & Keyboard Bindings

This guide lists the command-line commands and the corresponding keyboard shortcuts configured at the OS level to control the background Speech-to-Text utility.

---

## 🚀 Easy Alias Setup (Recommended)

To avoid typing the full python virtual environment path, add a shell alias `pstt` to your `~/.bashrc`:

```bash
echo 'alias pstt="/home/gourab/coding/personalStt/.venv/bin/python /home/gourab/coding/personalStt/main.py"' >> ~/.bashrc && source ~/.bashrc
```

Once defined, you can use `pstt` directly in your terminal.

---

## 🎹 Keyboard Bindings

Map these custom keyboard shortcuts in **Ubuntu Settings -> Keyboard -> Custom Shortcuts**:

| Shortcut Name            | Command                                                                                           | Key Combination |
| :----------------------- | :------------------------------------------------------------------------------------------------ | :-------------- |
| **PersonalSTT - Start**  | `/home/gourab/coding/personalStt/.venv/bin/python /home/gourab/coding/personalStt/main.py start`  | `Ctrl+Shift+D`  |
| **PersonalSTT - Stop**   | `/home/gourab/coding/personalStt/.venv/bin/python /home/gourab/coding/personalStt/main.py stop`   | `Ctrl+Shift+S`  |
| **PersonalSTT - Cancel** | `/home/gourab/coding/personalStt/.venv/bin/python /home/gourab/coding/personalStt/main.py cancel` | `Ctrl+Shift+Q`  |

> [!NOTE]
> Ensure the full path to `python` and `main.py` is used in the Ubuntu Settings UI command box, as shell aliases like `pstt` do not work outside of the terminal environment.

---

## 🛠️ CLI Commands Reference

All commands can be invoked using the `pstt` alias:

### 1. `pstt start`

Sends the `start` command to the running background daemon.

- **State Change:** `IDLE` ➔ `RECORDING`
- **Output:** Plays `start.wav` (high-pitch beep) and posts a desktop notification ("Listening...").

### 2. `pstt stop`

Sends the `stop` command to the running background daemon.

- **State Change:** `RECORDING` ➔ `TRANSCRIBING` ➔ `IDLE`
- **Output:** Plays `stop.wav` (lower beep), queries the Groq API, copies the text, simulates `Ctrl+V` to insert the text, and plays `success.wav` (double beep) on completion.

### 3. `pstt cancel`

Aborts any current recording or transcription.

- **State Change:** `RECORDING` / `TRANSCRIBING` ➔ `IDLE`
- **Output:** Plays `error.wav` (low warning buzz) and purges the temporary WAV audio file.

### 4. `pstt status`

Displays diagnostic status of the daemon socket and the systemd user service.

- **Output:** Prints state (`IDLE`, `RECORDING`, `TRANSCRIBING`) and indicates if the background daemon is healthy.

### 5. `pstt restart`

Restarts the systemd user service.

- **Command Executed:** `systemctl --user restart personalstt.service`

### 6. `pstt install`

Installs, registers, enables, and starts the background systemd service for the current user.

- **Unit File Path:** `~/.config/systemd/user/personalstt.service`

### 7. `--daemon`

Runs the daemon socket server loop directly. This is the command executed in the background by the systemd service.

### 8. `pstt config`

Manages the application configuration settings.

- **`pstt config list`**: Lists all configuration settings, current values, and descriptions.
- **`pstt config get <key>`**: Prints the value of a specific key.
- **`pstt config set <key> <value>`**: Updates a setting (validates the type and ranges, and dynamically notifies the daemon).

---

## ⚙️ Configuration Settings Reference

Settings are stored in standard JSON format at `~/.config/personalstt/config.json`. Below are the available keys:

| Config Key          | Default Value              | Type    | Description                                                                                                                                            |
| :------------------ | :------------------------- | :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `max_duration_sec`  | `240`                      | `int`   | Hard recording limit in seconds. Recording auto-cancels if it reaches this duration. Also rejects manual stops if the elapsed time exceeds this limit. |
| `groq_model`        | `"whisper-large-v3-turbo"` | `str`   | The Groq Whisper STT model used for transcribing.                                                                                                      |
| `api_retries`       | `3`                        | `int`   | Number of times to retry failed Groq API requests with exponential backoff.                                                                            |
| `alsa_device`       | `"default"`                | `str`   | ALSA audio input device passed to `arecord -D` (e.g. `default` or a hardware microphone interface).                                                    |
| `feedback_volume`   | `0.3`                      | `float` | Volume (0.0 to 1.0) of feedback beeps. Adjusting this automatically regenerates the sound assets.                                                      |
| `notify_timeout_ms` | `2000`                     | `int`   | Duration (in milliseconds) that desktop notifications stay visible.                                                                                    |
