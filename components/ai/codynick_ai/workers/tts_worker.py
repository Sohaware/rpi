"""Persistent legacy Coqui TTS worker process."""

from __future__ import annotations

import argparse
import socket
import traceback

from codynick_ai.protocol import receive_message, send_message


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True, dest="socket_path")
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--language", required=True, choices=("en",))
    args = parser.parse_args()

    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.connect(args.socket_path)
    stream = connection.makefile("rwb")
    try:
        send_message(stream, {"type": "loading", "app": "tts"})
        try:
            from .coqui_tts_engine import CoquiTtsEngine

            engine = CoquiTtsEngine(
                args.model_key,
                args.language,
            )
            send_message(
                stream,
                {
                    "type": "ready",
                    "app": "tts",
                    "language": engine.language,
                    "model_name": engine.model_key,
                    "speakers": list(engine.voices),
                    "speaker_map": engine.voices,
                    "default_speaker": "speaker1",
                    "library_load_sec": engine.load_seconds,
                },
            )
        except Exception as exc:
            send_message(
                stream,
                {
                    "type": "load_error",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            return 2

        while True:
            try:
                request = receive_message(stream)
            except EOFError:
                break
            request_id = request.get("id")
            command = request.get("command")
            arguments = request.get("arguments") or {}
            if command == "ping":
                result = {
                    "app": "tts",
                    "status": "ready",
                    "language": engine.language,
                    "model_name": engine.model_key,
                    "speakers": list(engine.voices),
                    "speaker_map": engine.voices,
                    "default_speaker": "speaker1",
                }
            elif command == "synthesize":
                result = engine.synthesize(**arguments)
            elif command == "shutdown":
                send_message(stream, {"id": request_id, "ok": True, "result": "shutdown"})
                break
            else:
                result = {
                    "ok": False,
                    "error_code": "INVALID_COMMAND",
                    "message": f"Unknown TTS worker command: {command}",
                }
            send_message(stream, {"id": request_id, "ok": True, "result": result})
    finally:
        try:
            stream.close()
        finally:
            connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
