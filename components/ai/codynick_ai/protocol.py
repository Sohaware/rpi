"""Small newline-delimited JSON protocol used on the private Unix socket."""

from __future__ import annotations

import json
from typing import Any, BinaryIO


def send_message(stream: BinaryIO, message: dict[str, Any]) -> None:
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    stream.write(payload.encode("utf-8") + b"\n")
    stream.flush()


def receive_message(stream: BinaryIO) -> dict[str, Any]:
    line = stream.readline()
    if not line:
        raise EOFError("The worker communication channel was closed.")
    message = json.loads(line.decode("utf-8"))
    if not isinstance(message, dict):
        raise ValueError("Protocol messages must be JSON objects.")
    return message
