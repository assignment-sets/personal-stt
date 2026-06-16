import os
import time
import socket
import threading
import subprocess
import groq
from personalstt.config import SOCKET_PATH, TEMP_WAV_PATH, get_api_key, load_config
from personalstt.sound import SoundEngine
from personalstt.recorder import AudioRecorder
from personalstt.transcriber import Transcriber
from personalstt.paster import ClipboardPaster


class RecordingDaemon:
    def __init__(self):
        self.state = "IDLE"
        self.sound = SoundEngine()
        self.recorder = AudioRecorder()
        self.paster = ClipboardPaster()
        self.cancel_flag = False
        self.recording_timer = None
        self.recording_start_time = None
        self.lock = threading.Lock()

    def show_notification(self, title, message, icon="media-record", urgency="normal"):
        """Displays a desktop notification using notify-send."""
        config = load_config()
        timeout_ms = config.get("notify_timeout_ms", 2000)
        try:
            cmd = ["notify-send", "-u", urgency]
            if urgency != "critical":
                cmd.extend(["-t", str(timeout_ms)])
            cmd.extend([f"--icon={icon}", title, message])

            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Failed to show notification: {e}")

    def _handle_timeout(self):
        """Automatically runs when safety timeout is reached."""
        print("Safety timeout reached. Auto-cancelling recording...")
        self.handle_cancel(reason="timeout")

    def handle_start(self):
        with self.lock:
            if self.state != "IDLE":
                print(f"Ignored start command. State is currently {self.state}.")
                return f"ERROR_ALREADY_{self.state}"

            config = load_config()
            alsa_device = config.get("alsa_device", "default")
            max_duration = config.get("max_duration_sec", 240)

            self.state = "RECORDING"
            self.cancel_flag = False
            self.recording_start_time = time.time()

            # Start safety timer
            self.recording_timer = threading.Timer(max_duration, self._handle_timeout)
            self.recording_timer.daemon = True
            self.recording_timer.start()

            self.sound.play("start")
            self.show_notification("PersonalSTT", "Listening...", "media-record")
            self.recorder.start_recording(TEMP_WAV_PATH, device=alsa_device)
            return "STARTED"

    def handle_stop(self):
        with self.lock:
            if self.state != "RECORDING":
                print(f"Ignored stop command. State is currently {self.state}.")
                return "ERROR_NOT_RECORDING"

            # Cancel safety timer
            if self.recording_timer:
                self.recording_timer.cancel()
                self.recording_timer = None

            elapsed_time = 0
            if self.recording_start_time:
                elapsed_time = time.time() - self.recording_start_time
                self.recording_start_time = None

            config = load_config()
            max_duration = config.get("max_duration_sec", 240)

            # Safety limit check: Discard if the actual duration exceeded limit
            if elapsed_time > (max_duration + 2.0):
                self.recorder.cancel_recording()
                self.state = "IDLE"
                self.sound.play("error")
                self.show_notification(
                    "PersonalSTT", "Discarded: Audio exceeds limit", "dialog-warning"
                )
                return "ERROR_EXCEEDED_MAX_DURATION"

            self.state = "TRANSCRIBING"
            self.sound.play("stop")
            self.show_notification("PersonalSTT", "Transcribing...", "document-send")

            # Gracefully stop recorder and retrieve filepath
            filepath = self.recorder.stop_recording()

            if filepath:
                # Dispatch transcription to a background thread to prevent blocking the IPC socket
                threading.Thread(
                    target=self._transcribe_thread, args=(filepath,), daemon=True
                ).start()
                return "STOPPING"
            else:
                self.state = "IDLE"
                self.sound.play("error")
                self.show_notification(
                    "PersonalSTT", "Recording failed: audio empty", "dialog-error"
                )
                return "ERROR_EMPTY_RECORDING"

    def handle_cancel(self, reason="manual"):
        with self.lock:
            # Cancel safety timer
            if self.recording_timer:
                self.recording_timer.cancel()
                self.recording_timer = None
            self.recording_start_time = None

            if self.state == "RECORDING":
                self.recorder.cancel_recording()
                self.state = "IDLE"
                self.sound.play("error")

                if reason == "timeout":
                    self.show_notification(
                        "PersonalSTT",
                        "Auto-cancelled: exceeded limit",
                        "dialog-warning",
                    )
                    return "AUTO_CANCELLED"
                else:
                    self.show_notification(
                        "PersonalSTT", "Recording cancelled", "dialog-warning"
                    )
                    return "CANCELLED_RECORDING"
            elif self.state == "TRANSCRIBING":
                self.cancel_flag = True
                self.state = "IDLE"
                self.sound.play("error")
                self.show_notification(
                    "PersonalSTT", "Transcription cancelled", "dialog-warning"
                )
                return "CANCELLED_TRANSCRIBING"
            else:
                return "IDLE"

    def handle_status(self):
        return self.state

    def _transcribe_thread(self, filepath):
        try:
            config = load_config()
            groq_model = config.get("groq_model", "whisper-large-v3-turbo")
            api_retries = config.get("api_retries", 3)
            api_key = get_api_key()

            # Instantiate transcriber with the fresh API key from environment
            transcriber = Transcriber(api_key)
            text = transcriber.transcribe(
                filepath, model=groq_model, max_retries=api_retries
            )

            with self.lock:
                if self.cancel_flag:
                    print("Transcription completed but user had cancelled it.")
                    return

                if text and text.strip():
                    cleaned_text = text.strip()
                    # Copy to X11 clipboard & paste
                    self.paster.copy(cleaned_text)
                    self.paster.paste()

                    self.sound.play("success")
                    self.show_notification(
                        "PersonalSTT", "Speech inserted!", "emblem-success"
                    )
                else:
                    self.sound.play("error")
                    self.show_notification(
                        "PersonalSTT", "No speech detected", "dialog-warning"
                    )
        except Exception as e:
            with self.lock:
                if not self.cancel_flag:
                    print(f"Error in transcription: {e}")
                    self.sound.play("error")

                    # Categorize Groq exception types
                    err_msg = str(e)
                    if isinstance(e, groq.AuthenticationError):
                        friendly_msg = "Authentication Failed: Please check your GROQ_CONF API Key."
                    elif isinstance(e, groq.RateLimitError):
                        friendly_msg = "Rate Limit Exceeded: Please wait a moment before trying again."
                    elif isinstance(e, groq.BadRequestError):
                        # Often contains quota details
                        friendly_msg = f"Request Error (Quota/Size limit):\n{err_msg}"
                    elif isinstance(e, groq.APIConnectionError):
                        friendly_msg = "Network Connection Error: Could not reach Groq. Check your internet connection."
                    elif isinstance(e, groq.APIError):
                        friendly_msg = f"Groq API Error: {err_msg}"
                    else:
                        friendly_msg = f"Unexpected Error: {err_msg}"

                    # Copy raw error description to clipboard
                    self.paster.copy(f"PersonalSTT Error Details:\n{err_msg}")

                    # Display persistent critical notification
                    self.show_notification(
                        "PersonalSTT Error",
                        f"{friendly_msg}\n(Details copied to clipboard)",
                        icon="dialog-error",
                        urgency="critical",
                    )
        finally:
            # Clean up temporary audio file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Failed to delete temp file {filepath}: {e}")

            with self.lock:
                if self.state == "TRANSCRIBING":
                    self.state = "IDLE"

    def run(self):
        """Runs the IPC Unix socket server loop."""
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
            except Exception as e:
                print(f"Could not remove stale socket {SOCKET_PATH}: {e}")
                return

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(SOCKET_PATH)
            server.listen(5)

            # Enable owner-only read/write access to the socket
            try:
                os.chmod(SOCKET_PATH, 0o600)
            except Exception as e:
                print(f"Failed to set socket permission: {e}")

            print(f"PersonalSTT Daemon listening on {SOCKET_PATH}...")

            while True:
                conn, _ = server.accept()
                try:
                    data = conn.recv(1024)
                    if data:
                        command = data.decode("utf-8").strip()
                        response = ""

                        if command == "start":
                            response = self.handle_start()
                        elif command == "stop":
                            response = self.handle_stop()
                        elif command == "cancel":
                            response = self.handle_cancel()
                        elif command == "status":
                            response = self.handle_status()
                        else:
                            response = f"UNKNOWN_COMMAND: {command}"

                        conn.sendall(response.encode("utf-8"))
                except Exception as e:
                    print(f"Error handling socket client: {e}")
                finally:
                    conn.close()
        except KeyboardInterrupt:
            print("Daemon stopping via manual KeyboardInterrupt.")
        except Exception as e:
            print(f"Daemon crashed: {e}")
        finally:
            server.close()
            if os.path.exists(SOCKET_PATH):
                try:
                    os.remove(SOCKET_PATH)
                except Exception:
                    pass
