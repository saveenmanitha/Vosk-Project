import time
from transcriber import VoskAudioTranscriber

# ==========================================
# HARDWARE CONFIGURATION (Raspberry Pi GPIO)
# ==========================================
# If running on Raspberry Pi, uncomment the RPi imports:
# import RPi.GPIO as GPIO
# RED_PIN = 17
# YELLOW_PIN = 27
# GREEN_PIN = 22
# GPIO.setmode(GPIO.BCM)
# GPIO.setup([RED_PIN, YELLOW_PIN, GREEN_PIN], GPIO.OUT, initial=GPIO.LOW)

def set_light(red: bool = False, yellow: bool = False, green: bool = False):
    """Controls the LED states (replace print statements with GPIO calls)."""
    # GPIO.output(RED_PIN, GPIO.HIGH if red else GPIO.LOW)
    # GPIO.output(YELLOW_PIN, GPIO.HIGH if yellow else GPIO.LOW)
    # GPIO.output(GREEN_PIN, GPIO.HIGH if green else GPIO.LOW)
    print(f"  [LED STATE] Red: {'ON' if red else 'OFF'} | Yellow: {'ON' if yellow else 'OFF'} | Green: {'ON' if green else 'OFF'}")

# State tracking for Green light
green_light_is_on = False

def handle_recognized_command(text: str):
    """Evaluates commands and manages the Green light."""
    global green_light_is_on
    text_lower = text.lower()

    if "turn on" in text_lower or "turn on light" in text_lower:
        green_light_is_on = True
        print("  --> Action: Light turned ON")
    elif "turn off" in text_lower or "turn off light" in text_lower:
        green_light_is_on = False
        print("  --> Action: Light turned OFF")
    else:
        print(f"  --> Recognized non-trigger text: '{text}'")

    # Green light stays in its current state (ON or OFF)
    set_light(red=False, yellow=False, green=green_light_is_on)


def run_batch_test(model_path: str, audio_folder: str):
    global green_light_is_on

    try:
        transcriber = VoskAudioTranscriber(model_path)
        audio_files = transcriber.get_audio_files(audio_folder)
    except FileNotFoundError as e:
        print(f"[FATAL ERROR] {e}")
        set_light(red=True, yellow=False, green=False)
        return

    print(f"\nProcessing {len(audio_files)} audio test files...\n")

    for file_path in audio_files:
        filename = file_path.split("\\")[-1]
        print(f"Testing: {filename}")

        try:
            transcript = transcriber.transcribe_file(file_path)

            if not transcript:
                # Yellow Light: No speech/text detected
                print("  --> Warning: No speech detected in audio file.")
                set_light(red=False, yellow=True, green=green_light_is_on)
            else:
                # Text detected: Evaluate command for Green Light
                print(f"  --> Detected: \"{transcript}\"")
                handle_recognized_command(transcript)

        except Exception as err:
            # Red Light: File corruption, invalid channels/sample rate, or read error
            print(f"  [ERROR] File issue: {err}")
            set_light(red=True, yellow=False, green=green_light_is_on)

        # Pause between files so you can observe the lights
        time.sleep(2)


if __name__ == "__main__":
    MODEL = r"C:\Users\samar\OneDrive\Documents\RasberryPi\vosk-model-small-en-us-0.15"
    FOLDER = r"C:\Users\samar\OneDrive\Documents\Audacity"

    try:
        run_batch_test(MODEL, FOLDER)
    finally:
        # If using Raspberry Pi GPIO:
        # GPIO.cleanup()
        pass