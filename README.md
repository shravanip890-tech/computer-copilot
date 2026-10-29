# Computer Copilot

A Windows-focused desktop voice assistant built with Python and Tkinter. The uploaded source includes voice commands, AI responses, common app/site launching, keyboard and mouse control, screenshots, Wikipedia lookups, camera-based hand/eye features, optional MySQL-backed face registration, and selectable UI themes.

## Features

- Voice input and spoken responses
- AI answers through the OpenAI API
- Quick launch for common websites and Windows applications
- Voice keyboard and computer-control commands
- Screenshot capture on Windows
- Wikipedia summaries
- MediaPipe face/hand landmark features
- Finger mouse and gesture-based volume control
- Optional MySQL-backed face registration/recognition
- Dark, Light, Cyber Blue, and Neon Purple themes

> **Platform note:** The source uses Windows-specific tools (`sapi5`, `pycaw`, PowerShell, `calc.exe`, and other Windows applications). Some features will not work on macOS/Linux without changes.

## Requirements

- Windows 10/11 recommended
- Python 3.10 or 3.11 recommended
- A microphone and camera for voice/camera features
- MySQL Server only if using face registration/recognition
- An OpenAI API key for AI answers

## Setup

1. Install Python from <https://www.python.org/downloads/>.
2. Clone or download this repository.
3. Open PowerShell in the repository folder.
4. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

5. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

6. Configure your OpenAI API key in the environment (do not commit it):

   ```powershell
   Copy `.env.example` to `.env`, then edit `.env` and set `OPENAI_API_KEY`. The app loads `.env` automatically. Do not commit `.env`.
   ```

7. Run the app:

   ```powershell
   python computer_copilot.py
   ```

## MediaPipe model files

The source downloads the following model files on first use and stores them in `models/`:

- `face_landmarker.task`
- `hand_landmarker.task`

An internet connection is needed for the first download.

## Optional MySQL setup

If you use face registration, install and start MySQL Server, create a dedicated local user/database as appropriate, and configure the connection settings in the source. Avoid using the MySQL root account for an application. MySQL settings can be configured with `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` in `.env`. Create a dedicated MySQL user with only the permissions the app needs; do not use the root account.

## Security and privacy notes

- Voice recognition sends audio to Google's speech-recognition service through the `SpeechRecognition` library.
- AI prompts are sent to the OpenAI API.
- Camera-based features process camera frames and face registration saves face images/landmark-derived data locally and in MySQL.
- Computer-control commands can type, click, and interact with your desktop. Use them only when you understand the command being executed.
- Do not commit API keys, personal face images, face data, database credentials, or other private information.
- Face recognition is not a secure substitute for Windows sign-in or other strong authentication.

## Example voice commands

- “Open YouTube” / “Open Google” / “Open Gmail”
- “What is the time?” / “What is today's date?”
- “Take screenshot”
- “Wikipedia Python”
- “Start finger mouse”
- “Start gesture volume”
- “Start eye detector”
- “Register my face” / “Face unlock”
- “Help” / “Stop listening” / “Exit”

Use the in-app Help window for the commands supported by the current source.

## Project structure

```text
computer-copilot/
├── computer_copilot.py
├── requirements.txt
├── .gitignore
├── .env.example
├── LICENSE
├── README.md
├── models/          # downloaded model files; not committed
└── face_images/     # local face images; not committed
```

## Known implementation note

The app defaults to `gpt-6-luna`; you can change this with `OPENAI_MODEL` in `.env`. Model availability depends on your OpenAI API account. Keep your API key in `.env` and never hard-code or commit secrets.

## License

This project includes a placeholder MIT license. Confirm that MIT is suitable for your project before publishing.
