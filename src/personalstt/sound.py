import os
import wave
import math
import struct
import subprocess
from personalstt.config import SOUND_DIR, load_config


class SoundEngine:
    def __init__(self):
        self.sound_dir = SOUND_DIR
        self._ensure_sounds_exist()

    def _ensure_sounds_exist(self):
        """Creates sound directory and generates default beeps if they don't exist."""
        os.makedirs(self.sound_dir, exist_ok=True)
        config = load_config()
        volume = config.get("feedback_volume", 0.3)

        sounds = {
            "start.wav": lambda f: self._generate_chirp(
                f, 600, 1000, 0.1, volume=volume
            ),
            "stop.wav": lambda f: self._generate_chirp(
                f, 1000, 600, 0.1, volume=volume
            ),
            "success.wav": lambda f: self._generate_double_beep(f, volume=volume),
            "error.wav": lambda f: self._generate_chirp(
                f, 200, 200, 0.3, volume=min(1.0, volume * 1.3)
            ),
        }

        for name, generator in sounds.items():
            path = os.path.join(self.sound_dir, name)
            if not os.path.exists(path):
                try:
                    generator(path)
                except Exception as e:
                    print(f"Failed to generate sound {name}: {e}")

    def _generate_chirp(
        self, filename, freq_start, freq_end, duration, sample_rate=8000, volume=0.3
    ):
        num_samples = int(duration * sample_rate)
        with wave.open(filename, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            phase = 0.0
            for i in range(num_samples):
                # Interpolate frequency
                freq = freq_start + (freq_end - freq_start) * (i / num_samples)
                phase += 2.0 * math.pi * freq / sample_rate
                value = int(volume * 32767.0 * math.sin(phase))
                wav_file.writeframesraw(struct.pack("<h", value))

    def _generate_double_beep(self, filename, sample_rate=8000, volume=0.3):
        with wave.open(filename, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            # First beep: 750Hz, 0.05s
            phase = 0.0
            for _ in range(int(0.05 * sample_rate)):
                phase += 2.0 * math.pi * 750 / sample_rate
                value = int(volume * 32767.0 * math.sin(phase))
                wav_file.writeframesraw(struct.pack("<h", value))

            # Silence: 0.03s
            for _ in range(int(0.03 * sample_rate)):
                wav_file.writeframesraw(struct.pack("<h", 0))

            # Second beep: 950Hz, 0.08s
            phase = 0.0
            for _ in range(int(0.08 * sample_rate)):
                phase += 2.0 * math.pi * 950 / sample_rate
                value = int(volume * 32767.0 * math.sin(phase))
                wav_file.writeframesraw(struct.pack("<h", value))

    def play(self, name):
        """Asynchronously plays a sound by name. Regenerates files if missing."""
        path = os.path.join(self.sound_dir, f"{name}.wav")
        if not os.path.exists(path):
            self._ensure_sounds_exist()

        if os.path.exists(path):
            try:
                subprocess.Popen(
                    ["aplay", "-q", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                print(f"Failed to play sound {name}: {e}")
        else:
            print(f"Sound file not found and could not be generated: {path}")
