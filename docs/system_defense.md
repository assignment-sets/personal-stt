# System Defense & Safety Guards: PersonalSTT

PersonalSTT operates directly at the OS level (managing subprocesses, audio capturing devices, clipboard interfaces, and keyboard injection). To guarantee system stability, security, and prevent hangs, the following defense and safety layers are implemented.

---

## 1. Process Isolation & Resource Boundaries

- **Subprocess Sandboxing:** Audio capturing is isolated inside a standard, battle-tested ALSA binary (`arecord`) spawned via `subprocess.Popen`. The Python interpreter does not hold open audio streams or manage raw memory buffers. A crash in the audio driver cannot corrupt the main Python daemon.
- **RAM-Only I/O (tmpfs):** Temporary audio files are written to `/tmp/personalstt_recording.wav`. In modern Ubuntu installations, `/tmp` is mapped in memory via `tmpfs`. This provides three critical benefits:
  1.  Zero disk write latency, preventing audio buffer overflows.
  2.  No physical disk/SSD writes, eliminating hardware wear.
  3.  If the system crashes, any left-over audio file is instantly cleared from RAM on reboot, preventing file leaks.

---

## 2. Safety Lockout Timers (Preventing Open Mics)

Leaving a microphone recording indefinitely is a significant privacy concern and can exhaust API quotas or crash filesystems.

- **Daemon-Side Timer:** When a recording starts, the daemon registers a `threading.Timer` matching the configured `max_duration_sec` (default 240 seconds).
- **Automatic Cancellation:** If the user fails to issue a stop or cancel command before the timer expires, the timer fires the cancellation handler:
  1.  Issues `SIGKILL` to `arecord`.
  2.  Deletes the temporary WAV file.
  3.  Plays the `error.wav` warning buzz.
  4.  Displays a desktop warning notification: _"Auto-cancelled: exceeded limit"_.
  5.  Transitions the daemon state back to `IDLE`.
- **Double-Safeguard Length check:** In case of race conditions, the daemon checks the actual elapsed recording time during manual stops. If the elapsed duration is greater than `max_duration_sec`, the audio is discarded, and the API request is rejected.

---

## 3. Control Group (CGroup) Sweeps (Preventing Zombie Processes)

If the main Python process crashes or gets killed, child processes (like `arecord` or `aplay`) can become orphaned "zombie" processes, keeping the microphone locked.

- **Systemd Management:** The background daemon runs as a systemd user service (`Type=simple`).
- **Automatic Cleanup:** When you run `pstt restart` or systemd terminates the daemon, systemd scans the dedicated Control Group (cgroup) associated with the service and automatically terminates **all** child processes in the tree. This guarantees that no microphone capturing process can survive a daemon crash.

---

## 4. Error Containment & Clipboard Debug Dumping

- **Asynchronous Thread Isolation:** The Groq API connection and pasting sequence are wrapped in a `try/except` block inside a separate daemon thread. Any network timeout, API authentication failure, or X11 pasting block is contained in that thread and cannot crash the main socket server daemon.
- **Smart Exception Translation:** When a Groq SDK API error occurs, the daemon catches specific exceptions and translates them to user-friendly notifications:
  - `groq.AuthenticationError` ➔ Authentication key issue.
  - `groq.RateLimitError` ➔ Rate limits exceeded.
  - `groq.BadRequestError` ➔ Quota / Parameters issues.
  - `groq.APIConnectionError` ➔ Network drops.
- **Clipboard Fallback Dump:** Standard Ubuntu notifications disappear quickly. To prevent "debugging in the dark", the daemon copies the **full raw traceback** and exception details to the system clipboard (`xclip`) on failure, and shows a persistent system notification (`-u critical`). You can immediately press `Ctrl+V` in any editor to see exactly why the call failed.
