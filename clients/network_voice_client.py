"""Optional laptop microphone client for the network voice server."""

import argparse
import json
import math
import queue
import array
import sys
import time
import urllib.error
import urllib.request
import wave
from io import BytesIO
from typing import Optional


class LaptopVoiceClient:
    def __init__(
        self,
        server_url: str,
        sample_rate: int = 16000,
        device: Optional[int] = None,
        silence_seconds: float = 0.8,
        threshold: int = 500,
        max_seconds: float = 6.0,
    ) -> None:
        if not server_url.startswith(("http://", "https://")):
            raise ValueError("server_url must start with http:// or https://")
        if sample_rate <= 0 or silence_seconds <= 0 or max_seconds <= 0:
            raise ValueError("Audio timing values must be greater than zero")
        try:
            import sounddevice as sd
        except ImportError as error:
            raise RuntimeError(
                "Install sounddevice on the laptop with: pip install sounddevice"
            ) from error

        self.sounddevice = sd
        self.server_url = server_url.rstrip("/") + "/audio"
        self.sample_rate = sample_rate
        self.device = device
        self.silence_seconds = silence_seconds
        self.threshold = threshold
        self.max_seconds = max_seconds

    def _record_utterance(self) -> bytes:
        chunks: queue.Queue[bytes] = queue.Queue()

        def callback(indata, frames, time_info, status) -> None:
            if status:
                print(f"[AUDIO WARNING] {status}", file=sys.stderr)
            chunks.put(bytes(indata))

        blocksize = 1024
        started = False
        silent_for = 0.0
        recorded_for = 0.0
        audio_chunks: list[bytes] = []
        with self.sounddevice.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=blocksize,
            dtype="int16",
            channels=1,
            device=self.device,
            callback=callback,
        ):
            while True:
                data = chunks.get()
                duration = len(data) / 2 / self.sample_rate
                samples = array.array("h")
                samples.frombytes(data)
                level = (
                    math.sqrt(sum(sample * sample for sample in samples) / len(samples))
                    if samples
                    else 0
                )
                if level >= self.threshold:
                    started = True
                    silent_for = 0.0
                elif started:
                    silent_for += duration
                if started:
                    audio_chunks.append(data)
                    recorded_for += duration
                if started and (
                    silent_for >= self.silence_seconds
                    or recorded_for >= self.max_seconds
                ):
                    return self._to_wav(audio_chunks)

    def _to_wav(self, chunks: list[bytes]) -> bytes:
        output = BytesIO()
        with wave.open(output, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(b"".join(chunks))
        return output.getvalue()

    def _send(self, audio: bytes) -> None:
        request = urllib.request.Request(
            self.server_url,
            data=audio,
            headers={"Content-Type": "audio/wav"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            print(f"[NETWORK ERROR] Could not reach Raspberry Pi: {error}")
            return
        print(f'[PI] "{result["transcript"]}" -> {result["command"]}')

    def run(self) -> None:
        print("Speak a command. Waiting for speech; press Ctrl+C to stop.")
        while True:
            self._send(self._record_utterance())
            time.sleep(0.1)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send laptop microphone commands to a Pi.")
    parser.add_argument("--server", required=True, help="Pi URL, e.g. http://192.168.1.50:8765")
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--threshold", type=int, default=500)
    parser.add_argument("--silence-seconds", type=float, default=0.8)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        LaptopVoiceClient(
            arguments.server,
            device=arguments.device,
            threshold=arguments.threshold,
            silence_seconds=arguments.silence_seconds,
        ).run()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Client stopped.")
        return 130
    except (RuntimeError, ValueError, OSError) as error:
        print(f"[STARTUP ERROR] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
