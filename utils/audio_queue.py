import os
import queue
import threading
import subprocess
import tempfile
import pyttsx3

class AudioQueue:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.lock = threading.Lock()
        #self.thread = threading.Thread(target=self.process_queue)
        #self.thread.start()

    def enqueue(self, audio_data):
        self.audio_queue.put(audio_data)
        self.play_next()

    def play_next(self):
        with self.lock:
            if not self.is_playing and not self.audio_queue.empty():
                self.is_playing = True
                audio_data = self.audio_queue.get()
                self.play_audio(audio_data)

    def play_audio(self, audio_data):
        # If audio_data is a path to an existing file, play it directly
        if isinstance(audio_data, str) and os.path.exists(audio_data):
            subprocess.run(["mpg123", "-q", audio_data], check=True)
            self.is_playing = False
            self.play_next()
            return

        # If audio_data is plain text, speak it via pyttsx3
        if isinstance(audio_data, str):
            try:
                engine = pyttsx3.init()
                engine.say(audio_data)
                engine.runAndWait()
            finally:
                self.is_playing = False
                self.play_next()
            return

        # Otherwise treat it as raw MP3 bytes
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
            fp.write(audio_data)
            fp.flush()
            subprocess.run(["mpg123", "-q", fp.name], check=True)
        self.is_playing = False
        self.play_next()

    def wait_until_empty(self):
        while not self.audio_queue.empty() or self.is_playing:
            pass  # Busy-wait until the queue is empty and current playback is done
