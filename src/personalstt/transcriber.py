import time
from groq import Groq


class Transcriber:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError(
                "Groq API key is missing. Please set the GROQ_CONF or GROQ_API_KEY environment variable, "
                "or place it in a local .env file."
            )
        self.client = Groq(api_key=api_key)

    def transcribe(self, filepath, model="whisper-large-v3-turbo", max_retries=3):
        """
        Sends the WAV audio file to the Groq Whisper transcription endpoint.
        Retries up to max_retries times with exponential backoff.
        """
        for attempt in range(max_retries):
            try:
                with open(filepath, "rb") as file:
                    transcription = self.client.audio.transcriptions.create(
                        file=(filepath, file.read()),
                        model=model,
                        temperature=0,
                        response_format="verbose_json",
                    )
                return transcription.text
            except Exception as e:
                print(f"Transcription attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2**attempt)
