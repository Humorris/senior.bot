import queue
import threading
import subprocess
import tempfile

class AudioQueue:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.process_queue)
        self.thread.start()

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
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
            fp.write(audio_data)
            fp.flush()
            subprocess.run(["mpg123", "-q", fp.name], check=True)
        self.is_playing = False
        self.play_next()

    def wait_until_empty(self):
        self.thread.join()  # Wait for the processing thread to finish
        while not self.audio_queue.empty():
            pass  # Wait until the queue is empty