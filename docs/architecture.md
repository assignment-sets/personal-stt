# System Architecture: PersonalSTT

PersonalSTT is built on a client-server architecture using Unix Domain Sockets for lightweight, low-latency Inter-Process Communication (IPC). The system registers a persistent background daemon via systemd, and interacts with it using a CLI wrapper triggered by global OS hotkeys.

---

## Component Architecture

```mermaid
graph TD
    subgraph Client Space (CLI)
        Hotkey[Ubuntu OS Hotkey] -->|Triggers| CLI[cli.py / main.py]
    end

    subgraph Daemon Space (Background Service)
        Socket[Unix Domain Socket Server] -->|Dispatches Command| Daemon[daemon.py]
        Daemon -->|Controls| Recorder[recorder.py]
        Daemon -->|Triggers Beeps| Sound[sound.py]
        Daemon -->|Spawns Thread| Transcriber[transcriber.py]
        Daemon -->|Pipes Output| Paster[paster.py]
    end

    subgraph OS & External Hardware
        Recorder -->|Spawns| arecord[ALSA arecord process]
        arecord -->|Writes WAV| TempDir[(/tmp/)]
        Sound -->|aplay -q| Speaker[System Speaker]
        Transcriber -->|HTTPS Request| Groq[Groq Whisper API]
        Paster -->|xclip stdin| Clipboard[X11 Clipboard]
        Paster -->|pynput Ctrl+V| ActiveWindow[Active Focused Window]
    end

    CLI -->|Socket Client| Socket
```

---

## State Machine

The daemon operates in three main states, coordinated using thread locks to prevent race conditions from concurrent key presses:

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> RECORDING : "start" command received
    RECORDING --> TRANSCRIBING : "stop" command received
    RECORDING --> IDLE : "cancel" command (manual or safety timeout)

    TRANSCRIBING --> IDLE : Transcription completed / failed / cancelled
```

### State Definitions

- **`IDLE`**: The daemon is sleeping, waiting for connections on the Unix socket. Resource consumption is effectively zero.
- **`RECORDING`**: The ALSA `arecord` process is active, streaming microphone input to `/tmp/personalstt_recording.wav`. A safety timer thread is running.
- **`TRANSCRIBING`**: `arecord` has terminated. A background thread is communicating with the Groq API. The socket is immediately freed to accept new commands, but the daemon state remains locked in `TRANSCRIBING` to reject new recording starts until pasting is complete.

---

## Execution Lifecycle Sequence

The sequence diagram below details the thread coordination and file flow when a user starts, stops, and receives a text insertion:

```mermaid
sequenceDiagram
    actor User
    participant OS as OS Shortcut Router
    participant Socket as Unix Domain Socket
    participant Daemon as Daemon Orchestrator
    participant Recorder as ALSA Recorder
    participant Groq as Groq Whisper API
    participant Paster as Clipboard Paster

    User->>OS: Press Ctrl+Shift+D (Start)
    OS->>Socket: Connect & Send "start"
    Socket->>Daemon: Acquire Lock & transition to RECORDING
    Daemon->>Daemon: Play start.wav (async) & notify "Listening"
    Daemon->>Recorder: Spawn 'arecord' subprocess to stream to /tmp/
    Daemon->>Daemon: Start safety timer thread (240s)
    Daemon-->>Socket: Return "STARTED"
    Socket-->>User: Exit CLI client (Instant)

    User->>OS: Press Ctrl+Shift+S (Stop)
    OS->>Socket: Connect & Send "stop"
    Socket->>Daemon: Transition state to TRANSCRIBING
    Daemon->>Daemon: Cancel safety timer thread
    Daemon->>Daemon: Play stop.wav (async) & notify "Transcribing"
    Daemon->>Recorder: Send SIGINT to 'arecord' (saves wav)
    Daemon-->>Socket: Return "STOPPING"
    Socket-->>User: Exit CLI client (Instant)

    Note over Daemon, Groq: Daemon dispatches transcription to background thread

    Daemon->>Groq: Read WAV & POST to Groq Whisper endpoint
    Groq-->>Daemon: Return transcribed text
    Daemon->>Paster: Copy text to X11 clipboard via xclip
    Daemon->>Paster: Simulate Ctrl+V key combination via pynput
    Paster-->>User: Text inserted at active cursor
    Daemon->>Daemon: Play success.wav (async) & notify "Success"
    Daemon->>Daemon: Delete temporary WAV file
    Daemon->>Daemon: Release Lock & transition to IDLE
```
