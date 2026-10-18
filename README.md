# 🎙️ Offline Voice-Controlled Light (Raspberry Pi + Vosk)

A lightweight, 100% offline speech recognition system running on a **Raspberry Pi**. It processes real-time voice commands through a USB microphone using the **Vosk API** and controls an LED or relay module via GPIO pins.

---

## 🌟 Key Features

- **100% Offline & Private:** No external cloud services or internet connection required. All speech inference runs locally on the Raspberry Pi.
- **Low Latency:** Uses a lightweight Vosk acoustic model optimized for ARM-based single-board computers.
- **Hardware Control:** Directly toggles Raspberry Pi GPIO pins upon detecting recognized trigger words (e.g., *"turn on the light"*, *"turn off"*).
- **Resource Efficient:** Built to run smoothly even on resource-constrained boards like the Raspberry Pi 3 or 4.

---

## 🛠️ Hardware Requirements

| Component | Description |
| :--- | :--- |
| **SBC** | Raspberry Pi (Pi 3B+, 4B, or 5 recommended) |
| **Microphone** | USB Microphone or USB Audio Sound Card with 3.5mm input |
| **Actuator** | 5V Relay module (for AC lights) or an LED with a 220Ω–330Ω resistor |
| **Wiring** | Breadboard and jumper wires |
| **Power Supply** | Standard Raspberry Pi power supply |

---

## 🔌 Circuit & Wiring (Example Pinout)

| Component Pin | Raspberry Pi Pin | Description |
| :--- | :--- | :--- |
| **Signal / Anode (+)** | **GPIO 22** (Physical Pin 15) | Output trigger pin |
| **GND (-)** | **GND** (Physical Pin 6 or Pin 9) | Ground reference (through 220Ω resistor for LED) |
| **VCC (If using Relay)** | **5V** (Physical Pin 2 or 4) | Power supply for relay coil |

---

## 📦 Installation & Setup

### 1. Update System & Install Dependencies
Open a terminal on your Raspberry Pi and run:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-dev portaudio19-dev libasound2-dev
```

### 2. Clone the Repository
```bash
git clone https://github.com/saveenmanitha/Vosk_Project.git
cd Vosk_Project
```

### 3. Install Python Libraries
```bash
pip3 install vosk sounddevice gpiozero
```
*(Alternatively, if you use a virtual environment, activate it before installing).*

---

## 🧠 Downloading the Vosk Speech Model

Vosk requires a local acoustic model to interpret audio data. For the Raspberry Pi, the lightweight English model is recommended:

```bash
# Download the small English model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip

# Unzip the archive
unzip vosk-model-small-en-us-0.15.zip

# Clean up zip archive
rm vosk-model-small-en-us-0.15.zip
```

Make sure your directory structure looks like this:
```text
Vosk_Project/
├── vosk-model-small-en-us-0.15/  # Extracted Vosk model files
├── live_voice_light_controller.py
└── README.md
```

The live controller uses the model directory shown above by default. If you
download a different model, pass its directory with `--model`.

---

## 🚀 Running the Project

### Live microphone control

Connect the microphone to the Raspberry Pi (for example, a USB microphone or
USB audio adapter). The speech recognition and GPIO control both run locally
on the Pi; nothing is sent to a cloud service.

1. **Verify your audio input device:**
   ```bash
   python3 -m sounddevice
   ```
   Take note of your USB microphone's device index if you need to specify it in `sounddevice.RawInputStream(device=...)`.

2. **Start the live controller:**
   ```bash
   python3 live_voice_light_controller.py
   ```
   To select a particular microphone:
   ```bash
   python3 live_voice_light_controller.py --device 2
   ```
   The controlled light/relay is connected to BCM GPIO 22 by default. For a
   relay module whose input is active-low, add `--active-low`.

3. **Speak into the microphone:**
   - 🗣️ **"turn on the light"** ➔ GPIO pin switches to `HIGH` (Light turns ON)
   - 🗣️ **"turn off the light"** ➔ GPIO pin switches to `LOW` (Light turns OFF)
   - Also supported: **"lights on"**, **"switch on"**, **"light off"**, and
     **"switch off"**.

Press `Ctrl+C` to stop. The controller turns the output off and releases the
GPIO resource during shutdown.

> A laptop's built-in microphone is not automatically available to a standalone
> Raspberry Pi. Use a microphone plugged into the Pi for this local design. If
> the microphone must remain in the laptop, an additional network audio
> streaming client/server would be required; that would move audio transport
> outside this project.

### Separate laptop-to-Raspberry-Pi network version

This version keeps the laptop microphone and moves the recognition/GPIO work to
the Pi:

```text
Laptop microphone
      │
      ▼
network_voice_client.py
      │  HTTP WAV upload over the same LAN
      ▼
network_voice_server.py on Raspberry Pi
      │
      ├── Vosk transcription on Pi
      ├── GPIO 22 → LED/relay
      └── GPIO 27 → yellow status LED
```

On the Raspberry Pi, find its LAN address with `hostname -I`, then start the
server:

```bash
pip3 install vosk gpiozero
python3 network_voice_server.py
```

The server listens on port `8765`. The yellow status LED uses BCM GPIO 27 by
default. It turns on when speech is recognized but the command is not a
supported ON/OFF light command, and turns off after a valid ON/OFF command.
If the relay is active-low:

```bash
python3 network_voice_server.py --active-low
```

If your yellow LED is wired to another BCM pin, specify it with
`--yellow-pin N`.

On the laptop, install the microphone client dependency:

```bash
pip install sounddevice
python network_voice_client.py --server http://PI_IP_ADDRESS:8765
```

Replace `PI_IP_ADDRESS` with the Pi address, for example:

```bash
python network_voice_client.py --server http://192.168.1.50:8765
```

The laptop client waits for speech, detects the end of the utterance using
silence, creates a short mono 16-bit WAV file in memory, and sends it to
`POST /audio`. The Pi returns the transcript and command result after Vosk
processing. Use `python -m sounddevice` on the laptop and pass `--device N` if
the desired microphone is not the default.

### Browser web application

The `web/` directory contains a dependency-free browser interface. The browser
records microphone audio using `MediaRecorder`, decodes it with the Web Audio
API, converts it to a mono 16-bit PCM WAV at 16 kHz, and sends it to the Pi's
`POST /audio` endpoint. This avoids requiring `ffmpeg` or another media
converter on the Raspberry Pi.

Start the Pi server as above, then serve the web directory from the laptop
(browsers generally block microphone access from a local `file://` page):

```bash
cd web
python3 -m http.server 8080
```

Open `http://localhost:8080` in a current browser, enter the Pi server URL
(for example `http://192.168.1.50:8765`), and select **Connect**. Allow
microphone access, record a command, and select **Stop recording** to send it.
The page displays the Vosk transcript, recognized action, response message,
light state, and yellow status LED state. The server provides `GET /status`
for the initial state and enables CORS for this LAN use.

This is intentionally a separate implementation from
`live_voice_light_controller.py`. Both versions use the same command parser,
but the network version does not send the Vosk model or GPIO operations to the
laptop. For a trusted home LAN, the server is sufficient; it has a payload size
limit and only accepts `POST /audio`, but it does not provide authentication or
encryption.

### Testing a recorded audio file

Use `audio_led_tester.py` to test the LED response from a WAV file without using
the microphone:

```bash
python3 audio_led_tester.py /home/pi/Vosk_Project/audio/lights_on.wav
```

The class-based tester exposes `check_light_command`,
`process_audio_file`, and `process_audio_folder` methods for reuse in future
applications. To test every WAV file in a directory:

```bash
python3 audio_led_tester.py --audio-folder /home/pi/Vosk_Project/audio
```

Use `--model /path/to/model` when the Vosk model is not at the default path.
Use `--hold-delay 0` for fast automated checks.

---

## ⚙️ How It Works

```text
Microphone Audio Input
        │
        ▼
PCM Stream (16kHz, 16-bit Mono)
        │
        ▼
Vosk Speech Recognizer (Kaldi Engine)
        │
        ▼
JSON Text Output Parsing (Keyword Match)
        │
        ▼
gpiozero GPIO Signal ──▶ Actuator (Relay / LED)
```

1. **Audio Ingestion:** Streams raw audio chunks in real-time through
   `sounddevice` from a microphone connected to the Pi.
2. **Offline Inference:** The Vosk model processes audio buffers locally on the Pi's CPU.
3. **Keyword Parsing:** Python parses the JSON output stream for trigger phrases.
4. **GPIO Actuation:** Sends a digital signal (`HIGH`/`LOW`) through
   `gpiozero` to control the connected circuit. Use `--active-low` for
   active-low relay boards.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/saveenmanitha/Vosk_Project/issues).

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).