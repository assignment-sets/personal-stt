# Codebase Guide: PersonalSTT

This document walks through the internal structure, module roles, and design details of the Python codebase located under `src/personalstt/`.

---

## Codebase Modules Breakdown

| Module                                                                                      | Core Responsibility                                  | Primary Classes / Functions                                                                                            |
| :------------------------------------------------------------------------------------------ | :--------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| **[config.py](file:///home/gourab/coding/personalStt/src/personalstt/config.py)**           | Configuration loader, Env parser, and Type Validator | `load_config()`, `save_config()`, `set_config_value(key, value)`, `get_api_key()`                                      |
| **[sound.py](file:///home/gourab/coding/personalStt/src/personalstt/sound.py)**             | Mathematical audio synthesis and playback            | `SoundEngine`, `_ensure_sounds_exist()`, `_generate_chirp()`, `play(name)`                                             |
| **[recorder.py](file:///home/gourab/coding/personalStt/src/personalstt/recorder.py)**       | Lifecycle wrapper for the ALSA recorder              | `AudioRecorder`, `start_recording(filepath, device)`, `stop_recording()`, `cancel_recording()`                         |
| **[transcriber.py](file:///home/gourab/coding/personalStt/src/personalstt/transcriber.py)** | Groq SDK client caller and retry engine              | `Transcriber`, `transcribe(filepath, model, max_retries)`                                                              |
| **[paster.py](file:///home/gourab/coding/personalStt/src/personalstt/paster.py)**           | X11 Clipboard and Keystroke Simulator                | `ClipboardPaster`, `copy(text)`, `paste()`                                                                             |
| **[daemon.py](file:///home/gourab/coding/personalStt/src/personalstt/daemon.py)**           | Unix Socket Server and State Orchestrator            | `RecordingDaemon`, `run()`, `_transcribe_thread(filepath)`, `handle_start()`, `handle_stop()`, `handle_cancel(reason)` |
| **[cli.py](file:///home/gourab/coding/personalStt/src/personalstt/cli.py)**                 | Command Router and systemd service builder           | `main()`, `send_command(cmd)`, `install_service()`, `print_status()`, `restart_service()`                              |

---

## Design Decisions & API Walkthrough

### 1. Dynamic Environment Resolution (`config.py`)

Because systemd user services run in isolated user-manager environments, they do not automatically inherit environment variables declared in the user's `~/.bashrc`.

- **Resolution:** The loader checks the environment first (`GROQ_CONF` and `GROQ_API_KEY`). If empty, it manually reads and parses a `.env` file in the project root.
- **Type validation:** Configurations set via `pstt config set <key> <value>` are cast dynamically to the expected python type of the default value (e.g. `int`, `float`, `str`). Out-of-bounds configurations (like volume > 1.0) are rejected before writing back to the JSON file.

### 2. Phase-Continuous Wave Synthesis (`sound.py`)

To prevent having to package static binary audio assets inside the repository, the sound engine synthesizes WAV beeps programmatically using raw math.

- **Chirp Generation (`_generate_chirp`):** Generates a sine wave beep. To prevent sound pop/clicks, it uses a **phase accumulator**:
  $$\text{Phase}_{i} = \text{Phase}_{i-1} + 2\pi \cdot \frac{\text{Freq}_i}{\text{SampleRate}}$$
  This guarantees phase continuity, creating smooth rising chirps (start beep) and falling chirps (stop beep).
- **On-Demand Synthesis:** When a configuration changes the `feedback_volume` parameter, the config manager deletes the local WAV files in `~/.local/share/personalstt/sounds/`. The sound engine regenerates them on-the-fly at the new volume level during the next playback.

### 3. Subprocess Lifecycle Management (`recorder.py`)

- `arecord` requires a graceful termination signal (`SIGINT`) to clean up its file buffer, write the final WAV file header (which contains the total sample size count), and close the file.
- If `arecord` hangs or takes longer than 2.0 seconds to terminate, the class catches the timeout and issues a hard `SIGKILL` to prevent locking the audio device (which would block other applications from using the microphone).

### 4. Lazy SDK Instantiation (`transcriber.py`)

To keep the daemon startup lightweight, we do not initialize the Groq client object when the daemon starts. It is instantiated inside the transcription thread only _after_ recording terminates. This also ensures that if you update your API key in `.env`, the next recording picks up the new key immediately without needing to restart the daemon.

### 5. Multi-Threaded Non-Blocking Socket Loop (`daemon.py`)

The Unix socket is the critical interface for global hotkeys. If it blocks, key events will hang.

- The socket loop reads the command, updates the state (`IDLE`, `RECORDING`, `TRANSCRIBING`), and writes the response back in milliseconds.
- The actual Groq transcription and pasting are executed on a separate daemon thread.
- **Locks:** A `threading.Lock` protects the daemon's internal state variables, ensuring that double-clicking a key shortcut cannot start overlapping subprocesses or trigger concurrent API uploads.
