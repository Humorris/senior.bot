# Raspberry Pi Voice and Face Assistant

This project combines voice recognition and face detection functionalities using a Raspberry Pi. It utilizes Google Text-to-Speech for audio output and manages wake word detection alongside face tracking.

## Project Structure

```
raspi-voice-face-assistant
├── src
│   ├── main.py              # Entry point of the application
│   ├── mix_module.py        # Handles wake word detection and voice commands
│   ├── camera_module.py     # Manages face detection and servo motor feedback
│   └── utils
│       └── audio_queue.py   # Utility for managing audio output queue
├── requirements.txt         # Lists project dependencies
├── .env.example             # Template for environment variables
└── README.md                # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd raspi-voice-face-assistant
   ```

2. **Install dependencies:**
   Ensure you have Python 3 installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in the required API keys and configurations.

4. **Run the application:**
   Execute the main script:
   ```bash
   python src/main.py
   ```

## Functionalities

- **Voice Assistant:**
  - Detects wake words and processes voice commands.
  - Provides audio feedback using Google Text-to-Speech.

- **Face Detection:**
  - Tracks the user's face and monitors attention levels.
  - Provides visual feedback through a servo motor when distractions are detected.

## Usage Guidelines

- Ensure your microphone and camera are properly connected to the Raspberry Pi.
- Adjust the sensitivity settings in the code if necessary to optimize performance based on your environment.
- Follow the on-screen prompts to interact with the voice assistant.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.