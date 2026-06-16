import subprocess
import time
from pynput.keyboard import Controller, Key


class ClipboardPaster:
    def __init__(self):
        self.keyboard = Controller()

    def copy(self, text):
        """Copies text to the system clipboard using xclip."""
        try:
            # -selection clipboard writes to the main system clipboard
            proc = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=text.encode("utf-8"))
            return True
        except Exception as e:
            print(f"Failed to copy to clipboard via xclip: {e}")
            return False

    def paste(self):
        """Simulates a Ctrl+V keyboard stroke to insert text at cursor position."""
        try:
            # Tiny delay to allow clipboard context to sync
            time.sleep(0.08)

            # Simulate Ctrl+V key combination
            self.keyboard.press(Key.ctrl)
            self.keyboard.press("v")
            self.keyboard.release("v")
            self.keyboard.release(Key.ctrl)
            return True
        except Exception as e:
            print(f"Failed to simulate paste via pynput: {e}")
            return False
