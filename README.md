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
| **Signal / Anode (+)** | **GPIO 17** (Physical Pin 11) | Output trigger pin |
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
pip3 install vosk sounddevice RPi.GPIO
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

# Rename the folder to 'model' so the code detects it
mv vosk-model-small-en-us-0.15 model

# Clean up zip archive
rm vosk-model-small-en-us-0.15.zip
```

Make sure your directory structure looks like this:
```text
Vosk_Project/
├── model/                # Extracted Vosk model files
├── main.py               # Main Python execution script
└── README.md
```

---

## 🚀 Running the Project

1. **Verify your audio input device:**
   ```bash
   python3 -m sounddevice
   ```
   Take note of your USB microphone's device index if you need to specify it in `sounddevice.RawInputStream(device=...)`.

2. **Execute the script:**
   ```bash
   python3 main.py
   ```

3. **Speak into the microphone:**
   - 🗣️ **"turn on the light"** ➔ GPIO pin switches to `HIGH` (Light turns ON)
   - 🗣️ **"turn off the light"** ➔ GPIO pin switches to `LOW` (Light turns OFF)

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
RPi.GPIO Signal ──▶ Actuator (Relay / LED)
```

1. **Audio Ingestion:** Streams raw audio chunks in real-time through `sounddevice`.
2. **Offline Inference:** The Vosk model processes audio buffers locally on the Pi's CPU.
3. **Keyword Parsing:** Python parses the JSON output stream for trigger phrases.
4. **GPIO Actuation:** Sends a digital signal (`HIGH`/`LOW`) to control the connected circuit.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/saveenmanitha/Vosk_Project/issues).

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).