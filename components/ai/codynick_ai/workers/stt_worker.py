"""Persistent Vosk worker with offline and background live recognition."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import threading
import traceback

from codynick_ai.protocol import receive_message, send_message


class LiveListening:
    def __init__(self, engine, event_stream):
        self.engine = engine
        self.event_stream = event_stream
        self.thread = None
        self.stop_event = threading.Event()
        self.process = None

    @property
    def active(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, *, mode, commands, min_confidence, device, sample_rate):
        if self.active:
            raise RuntimeError("Live speech recognition is already running")
        recognizer, mode, commands, threshold = self.engine.new_recognizer(
            mode=mode,
            commands=commands,
            min_confidence=min_confidence,
            sample_rate=sample_rate,
        )
        self.stop_event.clear()

        def emit(message):
            send_message(self.event_stream, message)

        def run():
            try:
                self.process = subprocess.Popen(
                    [
                        "arecord", "-q", "-D", device, "-t", "raw",
                        "-f", "S16_LE", "-r", str(sample_rate), "-c", "1",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                while not self.stop_event.is_set():
                    data = self.process.stdout.read(8000)
                    if not data:
                        if self.process.poll() is not None:
                            error = self.process.stderr.read().decode(
                                "utf-8", errors="replace"
                            ).strip()
                            raise RuntimeError(error or "arecord stopped unexpectedly")
                        continue
                    if recognizer.AcceptWaveform(data):
                        event = self.engine.result_from_json(
                            recognizer.Result(),
                            mode=mode,
                            commands=commands,
                            min_confidence=threshold,
                            event=True,
                        )
                        if event["text"]:
                            emit(event)
                final = self.engine.result_from_json(
                    recognizer.FinalResult(),
                    mode=mode,
                    commands=commands,
                    min_confidence=threshold,
                    event=True,
                )
                if final["text"]:
                    emit(final)
            except Exception as exc:
                if not self.stop_event.is_set():
                    emit(
                        {
                            "type": "speech_error",
                            "error_type": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
            finally:
                if self.process is not None and self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                self.process = None

        self.thread = threading.Thread(target=run, name="stt-live", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        if self.thread is not None:
            self.thread.join(timeout=3)
        self.thread = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True, dest="socket_path")
    parser.add_argument("--events", required=True, dest="event_socket_path")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--language", required=True)
    args = parser.parse_args()

    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.connect(args.socket_path)
    stream = connection.makefile("rwb")
    event_connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    event_connection.connect(args.event_socket_path)
    event_stream = event_connection.makefile("rwb")
    listener = None
    try:
        send_message(stream, {"type": "loading", "app": "stt"})
        try:
            from .vosk_engine import VoskSpeechRecognizer

            engine = VoskSpeechRecognizer(
                args.model_path,
                language=args.language,
                model_name=args.model_name,
            )
            listener = LiveListening(engine, event_stream)
            send_message(
                stream,
                {
                    "type": "ready",
                    "app": "stt",
                    "language": engine.language,
                    "model_name": engine.model_name,
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
            try:
                if command == "ping":
                    result = {
                        "app": "stt",
                        "status": "ready",
                        "language": engine.language,
                        "model_name": engine.model_name,
                        "listening": listener.active,
                    }
                elif command == "transcribe":
                    result = engine.transcribe(**arguments)
                elif command == "start_listening":
                    listener.start(**arguments)
                    result = {"listening": True}
                elif command == "stop_listening":
                    listener.stop()
                    result = {"listening": False}
                elif command == "shutdown":
                    listener.stop()
                    send_message(
                        stream, {"id": request_id, "ok": True, "result": "shutdown"}
                    )
                    break
                else:
                    raise ValueError(f"Unknown STT worker command: {command}")
                send_message(stream, {"id": request_id, "ok": True, "result": result})
            except Exception as exc:
                send_message(
                    stream,
                    {
                        "id": request_id,
                        "ok": False,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                )
    finally:
        if listener is not None:
            listener.stop()
        for resource in (event_stream, event_connection, stream, connection):
            try:
                resource.close()
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
