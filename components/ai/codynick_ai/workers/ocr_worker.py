"""Persistent Tesseract OCR worker process."""

from __future__ import annotations

import argparse
import socket
import traceback

from codynick_ai.protocol import receive_message, send_message


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True, dest="socket_path")
    parser.add_argument("--model", required=True, choices=("fast", "standard", "best"))
    parser.add_argument("--tessdata-dir")
    parser.add_argument("--language", action="append", dest="languages", required=True)
    args = parser.parse_args()

    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.connect(args.socket_path)
    stream = connection.makefile("rwb")
    try:
        send_message(stream, {"type": "loading", "app": "ocr"})
        try:
            from .tesseract_engine import TesseractOcrEngine

            engine = TesseractOcrEngine(
                args.languages,
                model_name=args.model,
                tessdata_directory=args.tessdata_dir,
            )
            send_message(
                stream,
                {
                    "type": "ready",
                    "app": "ocr",
                    "languages": engine.languages,
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
                        "app": "ocr",
                        "status": "ready",
                        "languages": engine.languages,
                        "model_name": engine.model_name,
                    }
                elif command == "read":
                    result = engine.read_text(**arguments)
                elif command == "shutdown":
                    send_message(
                        stream,
                        {"id": request_id, "ok": True, "result": "shutdown"},
                    )
                    break
                else:
                    raise ValueError(f"Unknown OCR worker command: {command}")
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
        try:
            stream.close()
        finally:
            connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
