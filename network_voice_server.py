"""Raspberry Pi server for laptop microphone voice commands.

The server receives short WAV recordings over the local network, transcribes
them with the local Vosk model, and controls the GPIO light.
"""

import argparse
import json
import sys
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from typing import Optional

from command_parser import check_light_command


class VoiceCommandServer:
    def __init__(
        self,
        model_path: str,
        light_pin: int = 22,
        active_low: bool = False,
        max_audio_bytes: int = 2_000_000,
    ) -> None:
        try:
            from gpiozero import LED
            from vosk import KaldiRecognizer, Model, SetLogLevel
        except ImportError as error:
            raise RuntimeError(
                "Install dependencies on the Pi with: "
                "pip3 install vosk gpiozero"
            ) from error

        if max_audio_bytes <= 0:
            raise ValueError("max_audio_bytes must be greater than zero")
        SetLogLevel(-1)
        self.max_audio_bytes = max_audio_bytes
        self.model = Model(model_path)
        self.light = LED(light_pin, active_high=not active_low)
        self.light.off()
        self._recognizer_type = KaldiRecognizer

    def process_wav(self, audio_bytes: bytes) -> dict[str, str]:
        if len(audio_bytes) > self.max_audio_bytes:
            raise ValueError("Audio recording is too large")

        with wave.open(BytesIO(audio_bytes), "rb") as wav_file:
            if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2:
                raise ValueError("Audio must be mono, 16-bit PCM WAV")
            recognizer = self._recognizer_type(self.model, wav_file.getframerate())
            while data := wav_file.readframes(4000):
                recognizer.AcceptWaveform(data)
            result = json.loads(recognizer.FinalResult())

        transcript = result.get("text", "").strip()
        command = check_light_command(transcript)
        if command == "ON":
            self.light.on()
        elif command == "OFF":
            self.light.off()

        return {"transcript": transcript, "command": command}

    def close(self) -> None:
        self.light.off()
        self.light.close()


def make_handler(controller: VoiceCommandServer):
    class RequestHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/audio":
                self.send_error(404, "Use POST /audio")
                return

            content_length_header = self.headers.get("Content-Length")
            try:
                content_length = int(content_length_header or "0")
            except ValueError:
                self.send_error(400, "Content-Length must be an integer")
                return
            if content_length <= 0 or content_length > controller.max_audio_bytes:
                self.send_error(413, "Invalid or oversized audio payload")
                return

            try:
                result = controller.process_wav(self.rfile.read(content_length))
            except (OSError, ValueError, wave.Error) as error:
                self.send_error(400, str(error))
                return

            response = json.dumps(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            print(
                f'[REQUEST] "{result["transcript"]}" -> {result["command"]}',
                flush=True,
            )

        def log_message(self, format: str, *args) -> None:
            print(f"[HTTP] {format % args}", file=sys.stderr)

    return RequestHandler


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Receive laptop voice recordings and control a Pi GPIO light."
    )
    parser.add_argument("--model", default="/home/pi/Vosk_Project/vosk-model-small-en-us-0.15")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to listen on")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--light-pin", type=int, default=22)
    parser.add_argument("--active-low", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    controller: Optional[VoiceCommandServer] = None
    server: Optional[ThreadingHTTPServer] = None
    try:
        controller = VoiceCommandServer(
            arguments.model, arguments.light_pin, arguments.active_low
        )
        server = ThreadingHTTPServer(
            (arguments.host, arguments.port), make_handler(controller)
        )
        print(
            f"Listening for laptop audio on http://{arguments.host}:{arguments.port}/audio"
        )
        server.serve_forever()
        return 0
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server stopped.")
        return 130
    except (OSError, RuntimeError, ValueError) as error:
        print(f"[STARTUP ERROR] {error}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.server_close()
        if controller is not None:
            controller.close()


if __name__ == "__main__":
    raise SystemExit(main())
