"""Persistent YOLO worker process for the VHL controller."""

from __future__ import annotations

import argparse
import socket
import traceback

from codynick_ai.protocol import receive_message, send_message


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True, dest="socket_path")
    parser.add_argument("--model", required=True, dest="model_path")
    parser.add_argument("--warmup", action="store_true")
    args = parser.parse_args()

    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.connect(args.socket_path)
    stream = connection.makefile("rwb")

    try:
        send_message(stream, {"type": "loading", "app": "yolo"})
        try:
            from .yolo_engine import YoloObjectDetector

            detector = YoloObjectDetector(args.model_path)
            warmup_seconds = detector.warmup() if args.warmup else 0.0
            send_message(
                stream,
                {
                    "type": "ready",
                    "app": "yolo",
                    "model": str(detector.model_path),
                    "library_load_sec": detector.load_seconds,
                    "warmup_sec": warmup_seconds,
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
                        "app": "yolo",
                        "status": "ready",
                        "model": str(detector.model_path),
                    }
                elif command == "detect":
                    result = detector.detect(**arguments)
                elif command == "shutdown":
                    send_message(
                        stream,
                        {"id": request_id, "ok": True, "result": "shutdown"},
                    )
                    break
                else:
                    raise ValueError(f"Unknown YOLO worker command: {command}")
                send_message(
                    stream, {"id": request_id, "ok": True, "result": result}
                )
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
