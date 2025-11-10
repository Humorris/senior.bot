import os
import threading
import time
from mix_module import initialize, detect_wake_word, process_voice_command
from camera_module import initialize_camera, process_video_frames
from utils.audio_queue import AudioQueue

def main():
    # Initialize Google Text-to-Speech
    initialize()

    # Initialize audio queue for managing audio outputs
    audio_queue = AudioQueue()

    # Start the camera processing in a separate thread
    camera_thread = threading.Thread(target=process_video_frames, args=(audio_queue,))
    camera_thread.start()

    # Main loop for wake word detection and voice command processing

    error_count = 0
    max_errors = 3

    while True:
        wake_word_detected = detect_wake_word()
        if wake_word_detected:
            error_count = 0  # 重置錯誤計數
            audio_queue.enqueue("Please say your command.")
            command = process_voice_command()
            if command:
                audio_queue.enqueue(command)
        else:
            error_count += 1
            if error_count >= max_errors:
                print(f"⚠️ Wake word detection failed {max_errors} times. Waiting 5 seconds before retry...")
                time.sleep(5)  # 等待 5 秒後再重試
                error_count = 0

if __name__ == "__main__":
    main()
