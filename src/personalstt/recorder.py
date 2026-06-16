import os
import signal
import subprocess


class AudioRecorder:
    def __init__(self):
        self.process = None
        self.filepath = None

    def start_recording(self, filepath, device="default"):
        """Starts recording audio to the specified filepath using the chosen device."""
        if self.process is not None:
            self.cancel_recording()

        self.filepath = filepath

        # Ensure target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Failed to remove old recording file: {e}")

        # Spawn arecord subprocess
        # -q: quiet
        # -D device: custom input device (default, hw:0, etc.)
        # -f S16_LE: signed 16-bit little-endian
        # -r 16000: 16kHz sample rate (optimal for whisper)
        # -c 1: mono
        try:
            self.process = subprocess.Popen(
                [
                    "arecord",
                    "-q",
                    "-D",
                    device,
                    "-f",
                    "S16_LE",
                    "-r",
                    "16000",
                    "-c",
                    "1",
                    filepath,
                ]
            )
        except Exception as e:
            print(f"Failed to start arecord process: {e}")
            self.process = None

    def stop_recording(self):
        """Gracefully stops recording, ensuring the WAV header is written."""
        if self.process is None:
            return None

        filepath = self.filepath
        try:
            # arecord needs SIGINT to flush header and stop recording cleanly
            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=2.0)
        except Exception as e:
            print(f"Error stopping arecord gracefully: {e}")
            try:
                self.process.kill()
                self.process.wait()
            except Exception:
                pass
        finally:
            self.process = None
            self.filepath = None

        # Return path if file is valid
        if filepath and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath
        return None

    def cancel_recording(self):
        """Stops recording immediately and deletes the temporary audio file."""
        if self.process is None:
            return

        filepath = self.filepath
        try:
            self.process.kill()
            self.process.wait(timeout=1.0)
        except Exception as e:
            print(f"Error killing recording process: {e}")
        finally:
            self.process = None
            self.filepath = None

        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting cancelled recording file: {e}")
