import os
from dotenv import load_dotenv
import google.generativeai as genai
import time
import tempfile
import subprocess
import speech_recognition as sr
import pvporcupine
from pvporcupine import Porcupine
import struct
import pyaudio
from google.cloud import texttospeech
from utils.audio_queue import AudioQueue

# Initialize audio queue
audio_queue = AudioQueue()

# --- Initialize Google Cloud TTS Client ---
tts_client = None
try:
    tts_client = texttospeech.TextToSpeechClient()
    print("Google Cloud Text-to-Speech client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize Google Cloud Text-to-Speech client: {e}")

# --- Load .env file ---
load_dotenv()

# --- Set up Gemini API ---
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"Failed to configure Gemini API: {e}")
    exit()

# --- Set up Porcupine wake word detection ---
PORCUPINE_ACCESS_KEY = os.environ.get("PORCUPINE_ACCESS_KEY")
if not PORCUPINE_ACCESS_KEY:
    print("Error: Please set PORCUPINE_ACCESS_KEY in the .env file.")
    exit()

WAKE_WORD_PATH = "/home/pi/欸學長.ppn"
PORCUPINE_LIBRARY_PATH = "/home/pi/.local/lib/python3.11/site-packages/pvporcupine/lib/raspberry-pi/cortex-a76-aarch64/libpv_porcupine.so"
PORCUPINE_MODEL_PATH = "/home/pi/Desktop/zh.pv"
WAKE_WORD_SENSITIVITY = 0.7

# --- Voice output function ---
def speak(text):
    print(f"Assistant: {text}")
    if tts_client is None:
        print("Voice service not started, unable to play audio.")
        return

    audio_file = "/tmp/response.mp3"
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_selection = texttospeech.VoiceSelectionParams(
            language_code='zh-TW',
            name='cmn-TW-Wavenet-C',
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice_selection, audio_config=audio_config
        )

        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
            fp.write(response.audio_content)
            fp.flush()
            audio_queue.enqueue(fp.name)

    except Exception as e:
        print(f"Error in TTS synthesis or playback: {e}")

# --- Wake word detection and command processing ---
def detect_wake_word():
    porcupine = None
    pa = None
    audio_stream = None

    try:
        porcupine = Porcupine(
            access_key=PORCUPINE_ACCESS_KEY,
            library_path=PORCUPINE_LIBRARY_PATH,
            model_path=PORCUPINE_MODEL_PATH,
            keyword_paths=[WAKE_WORD_PATH],
            sensitivities=[WAKE_WORD_SENSITIVITY]
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print("Waiting for wake word...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word detected! Please give your command.")
                recognized_text = get_audio_input()
                if recognized_text:
                    gemini_output = get_gemini_response(recognized_text)
                    speak(gemini_output)
                else:
                    speak("No valid command received, please try again.")

    except Exception as e:
        print(f"Error in wake word detection: {e}")
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()

# --- Audio input function ---
def get_audio_input():
    r = sr.Recognizer()
    r.pause_threshold = 1.0
    with sr.Microphone() as source:
        print("Microphone calibrated, please start speaking...")
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, phrase_time_limit=None)
            print("Recording complete, recognizing...")
            text = r.recognize_google(audio, language="zh-TW")
            print(f"Recognition result: {text}")
            return text
        except Exception as e:
            print(f"Error in audio input: {e}")
            return None

# --- Gemini response function ---
def get_gemini_response(prompt_text):
    if not prompt_text:
        return "No valid input received, Gemini cannot respond."

    print(f"Sending '{prompt_text}' to Gemini...")
    max_retries = 3
    initial_delay = 2
    instruction_prompt = f"Please respond concisely in under 200 words: {prompt_text}"
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    candidate_count=1,
                )
            )
            return response.text
        except Exception as e:
            print(f"Gemini API request error: {e}")
            return "Sorry, Gemini API is temporarily unavailable."

# --- Initialize functions ---
def initialize():
    detect_wake_word()  # Start wake word detection

# Export functions
if __name__ == "__main__":
    initialize()