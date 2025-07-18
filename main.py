import os
import threading
from mix_module import initialize_tts, detect_wake_word, process_voice_command
from camera_module import initialize_camera, process_video_frames
from utils.audio_queue import AudioQueue

def main():
    # Initialize Google Text-to-Speech
    initialize_tts()

    # Initialize audio queue for managing audio outputs
    audio_queue = AudioQueue()

    # Start the camera processing in a separate thread
    camera_thread = threading.Thread(target=process_video_frames, args=(audio_queue,))
    camera_thread.start()

    # Main loop for wake word detection and voice command processing
    while True:
        wake_word_detected = detect_wake_word()
        if wake_word_detected:
            audio_queue.enqueue("Please say your command.")
            command = process_voice_command()
            if command:
                audio_queue.enqueue(command)

if __name__ == "__main__":
    main()