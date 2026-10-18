import os
import wave
import json
from pathlib import Path
from vosk import Model, KaldiRecognizer, SetLogLevel

# Silence Kaldi debug logs (-1)
SetLogLevel(-1)

class VoskAudioTranscriber:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model path does not exist: {model_path}")
        print("Loading Vosk model into memory...")
        self.model = Model(model_path)

    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribes a WAV file.
        Raises ValueError or wave.Error if the file is invalid/corrupt.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        wf = wave.open(audio_path, "rb")
        try:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()

            if channels != 1:
                raise ValueError(f"Expected Mono (1 channel), got {channels}")
            if sample_width != 2:
                raise ValueError(f"Expected 16-bit PCM (2 bytes), got {sample_width}")

            recognizer = KaldiRecognizer(self.model, sample_rate)
            segments = []
            CHUNK = 4000

            while True:
                data = wf.readframes(CHUNK)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    text = res.get("text", "").strip()
                    if text:
                        segments.append(text)

            final_res = json.loads(recognizer.FinalResult())
            trailing_text = final_res.get("text", "").strip()
            if trailing_text:
                segments.append(trailing_text)

            return " ".join(segments).strip()
        finally:
            wf.close()

    def get_audio_files(self, folder_path: str) -> list[str]:
        """Finds all .wav files in the folder."""
        folder = Path(folder_path)
        if not folder.is_dir():
            raise FileNotFoundError(f"Audio folder not found: {folder_path}")
        return [str(p) for p in folder.glob("*.wav")]