# Agent Onboarding Guide: PersonalSTT

Welcome, AI Agent! This document acts as your primary knowledge transfer entrypoint for contributing to the **PersonalSTT** project. 

PersonalSTT is a lightweight, zero-GUI background Speech-to-Text daemon for Ubuntu X11 sessions. It captures audio using `arecord`, transcribes it via the Groq Whisper API, and simulates keyboard pasting (`Ctrl+V`) to type the transcription at the active cursor position.

---

## 📂 Project Directory Structure

```
personalStt/
├── pyproject.toml         # Package settings, dependencies (groq, pynput), and build targets
├── uv.lock                # Locked python dependencies
├── main.py                # Root entry point delegating to src/personalstt/cli.py
├── .env                   # Local credentials (contains GROQ_CONF="your_api_key")
├── README.md              # Public user-facing project instructions
├── AGENT.md               # You are here (AI Agent onboarding entrypoint)
├── docs/                  # Specialized developer guides
│   ├── architecture.md    # Component models and Mermaid lifecycle sequence diagrams
│   ├── codebase.md        # Detailed codebase module and API breakdown
│   ├── cli_guide.md       # CLI commands and configuration settings reference
│   └── system_defense.md  # OS-level safety, cgroup sweeps, and timeout defenses
└── src/
    └── personalstt/       # Core package implementation
        ├── __init__.py    # Versioning metadata
        ├── config.py      # Env parsing, defaults config manager, and validation
        ├── sound.py       # Wave generator (beep synthesis) and async player
        ├── recorder.py    # Subprocess controller for ALSA arecord
        ├── transcriber.py # Groq Whisper SDK client wrapper with retries
        ├── paster.py      # xclip and pynput X11 pasting engine
        ├── daemon.py      # Unix socket server, state machine, and thread dispatcher
        └── cli.py         # Subcommand router and systemd user service installer
```

---

## 📖 Reference Documentation

To dive into specific modules or design implementations, follow these relative links:

1.  **[System Architecture & Diagrams](docs/architecture.md):** Learn about the client-server IPC model, the daemon state machine, and view sequence diagrams of the recording and transcription flow.
2.  **[Codebase Modules Guide](docs/codebase.md):** Deep-dive into each Python module under `src/personalstt/`, review class interfaces, and study the dynamic API key loading and wave audio synthesis logic.
3.  **[CLI & Configuration Reference](docs/cli_guide.md):** Review the subcommands (start, stop, cancel, status, restart, install, config) and study the JSON config keys stored at `~/.config/personalstt/config.json`.
4.  **[System Defenses & Robustness](docs/system_defense.md):** Understand the safety timer lockouts, cgroup sweeping under systemd, X11 clipboard error trace dumps, and thread safety.

---

## 🛠️ Contribution Recipes

Follow these recipes when extending the codebase to ensure consistency:

### Recipe A: Adding a New Configuration Parameter
1. Open [config.py](src/personalstt/config.py) and add the parameter with its default value to the `DEFAULT_CONFIG` dictionary.
2. Add a description for the new parameter in `CONFIG_DESCRIPTIONS`.
3. In `set_config_value()`, verify if any type casting or bounds validation (like range checks) is required.
4. Access the setting inside [daemon.py](src/personalstt/daemon.py) by calling `config = load_config()` followed by `config.get("your_key")`.

### Recipe B: Introducing a New Audio Feedback Beep
1. Open [sound.py](src/personalstt/sound.py).
2. Inside `_ensure_sounds_exist()`, define a generator function mapping for the new sound file (e.g. `chirp` or `double_beep`).
3. Call the generator inside the `sounds` dict mapping.
4. Trigger the new beep inside [daemon.py](src/personalstt/daemon.py) by calling `self.sound.play("new_sound_name")`.

### Recipe C: Modifying State Machine Flows
1. Open [daemon.py](src/personalstt/daemon.py).
2. Review the states handled by the `RecordingDaemon` (currently `IDLE`, `RECORDING`, `TRANSCRIBING`).
3. If adding a new state, ensure you obtain the lock (`with self.lock:`) before checking or updating `self.state`.
4. If the new state involves an asynchronous task, spawn it inside a background thread (`threading.Thread`) so you do not block the main Unix Domain Socket loop.
