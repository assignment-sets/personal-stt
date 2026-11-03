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

## 🛠️ CLI Commands & Options Reference

All commands can be invoked using the `pstt` alias:

### Standard Options
- **`-h`, `--help`**: Print help and command usage summary.
- **`-v`, `--version`**: Print the installed PersonalSTT version.

### 1. `pstt start`

Sends the `start` command to the running background daemon.

- **State Change:** `IDLE` ➔ `RECORDING`
- **Output:** Plays `start.wav` (high-pitch beep) and posts a desktop notification ("Listening...").

### 2. `pstt stop [-c | --copy-only]`

Sends the `stop` command to the running background daemon.

- **State Change:** `RECORDING` ➔ `TRANSCRIBING` ➔ `IDLE`
- **Flags:**
  - `-c`, `--copy-only`: Only copy transcription to system clipboard without simulating `Ctrl+V`.
- **Output:** Plays `stop.wav` (lower beep), queries Groq Whisper, copies text to clipboard, simulates `Ctrl+V` (if auto-paste is active and not copy-only), and plays `success.wav`.

### 3. `pstt cancel`

Aborts any current recording or transcription.

- **State Change:** `RECORDING` / `TRANSCRIBING` ➔ `IDLE`
- **Output:** Plays `error.wav` (low warning buzz) and purges the temporary WAV audio file.

### 4. `pstt status`

Displays diagnostic status of the daemon socket and the systemd user service.

- **Output:** Prints state (`IDLE`, `RECORDING`, `TRANSCRIBING`) and indicates if the background daemon is healthy.

### 5. `pstt logs [-f] [-n <num>]`

Displays output logs from the background daemon using systemd's `journalctl`.

- **Flags:**
  - `-f`, `--follow`: Stream logs in real time.
  - `-n <num>`: Limit output to the last `<num>` lines (e.g. `pstt logs -n 50`).

### 6. `pstt restart`

Restarts the systemd user service.

- **Command Executed:** `systemctl --user restart personalstt.service`

### 7. `pstt install`

Installs, registers, enables, and starts the background systemd service for the current user.

- **Unit File Path:** `~/.config/systemd/user/personalstt.service`

### 8. `--daemon`

Runs the daemon socket server loop directly. This is the command executed in the background by the systemd service.

### 9. `pstt config`

Manages the application configuration settings.

- **`pstt config list`**: Lists all configuration settings, current values, and descriptions.
- **`pstt config get <key>`**: Prints the value of a specific key.
- **`pstt config set <key> <value>`**: Updates a setting (validates the type and ranges).

---

## ⚙️ Configuration Settings Reference

Settings are stored in standard JSON format at `~/.config/personalstt/config.json`. Below are the available keys:

| Config Key          | Default Value              | Type    | Description                                                                                                                                            |
| :------------------ | :------------------------- | :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `max_duration_sec`  | `300`                      | `int`   | Hard recording limit in seconds. Recording auto-cancels if it reaches this duration. Also rejects manual stops if the elapsed time exceeds this limit. |
| `groq_model`        | `"whisper-large-v3-turbo"` | `str`   | The Groq Whisper STT model used for transcribing (`whisper-large-v3-turbo`, `whisper-large-v3`).                                                      |
| `language`          | `"en"`                     | `str`   | Spoken audio language code (e.g. `en`, `es`, `fr`, or empty `""` for Whisper auto-detection). Setting this reduces Groq inference latency.          |
| `prompt`            | `""`                       | `str`   | Optional domain vocabulary, technical jargon, or punctuation context passed to Groq Whisper.                                                          |
| `auto_paste`        | `true`                     | `bool`  | Whether to automatically simulate Ctrl+V to paste into the active window (`true`/`false`).                                                             |
| `api_retries`       | `3`                        | `int`   | Number of times to retry failed Groq API requests with exponential backoff.                                                                            |
| `alsa_device`       | `"default"`                | `str`   | ALSA audio input device passed to `arecord -D` (e.g. `default` or a hardware microphone interface).                                                    |
| `feedback_volume`   | `0.3`                      | `float` | Synthesized feedback audio cues volume level (`0.0` to `1.0`).                                                                                         |
| `notify_timeout_ms` | `2000`                     | `int`   | Duration (in milliseconds) desktop notifications stay on screen.                                                                                       |
| `feedback_volume`   | `0.3`                      | `float` | Volume (0.0 to 1.0) of feedback beeps. Adjusting this automatically regenerates the sound assets.                                                      |
| `notify_timeout_ms` | `2000`                     | `int`   | Duration (in milliseconds) that desktop notifications stay visible.                                                                                    |
