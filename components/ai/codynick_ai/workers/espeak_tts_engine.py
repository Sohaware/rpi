"""Small offline eSpeak-NG synthesis engine for CodyNick Rev.B2."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import wave
from pathlib import Path


SPEAKERS = ("speaker1", "speaker2", "speaker3")
VOICE_MAP = {
    "en": {"speaker1": "en-us", "speaker2": "en-us+m3", "speaker3": "en-us+f3"},
    "fr": {"speaker1": "fr-fr", "speaker2": "fr-fr+m3", "speaker3": "fr-fr+f3"},
    "ar": {"speaker1": "ar", "speaker2": "ar+m3", "speaker3": "ar+f3"},
}


def error(code: str, message: str, **details) -> dict:
    return {"ok": False, "error_code": code, "message": message, **details}


class EspeakTtsEngine:
    def __init__(self, model_key: str, language: str):
        started = time.perf_counter()
        executable = shutil.which("espeak-ng")
        if executable is None:
            raise FileNotFoundError("eSpeak-NG is not installed.")
        if language not in VOICE_MAP:
            raise ValueError("Choose TTS language: en, fr, or ar.")
        self.executable = executable
        self.model_key = model_key
        self.language = language
        self.voices = VOICE_MAP[language]
        self.load_seconds = time.perf_counter() - started

    def synthesize(
        self,
        *,
        text: str,
        speaker: str,
        output_path: str,
        current_path: str,
        json_path: str,
    ) -> dict:
        if not isinstance(text, str) or not text.strip():
            return error("EMPTY_TEXT", "Provide some text to synthesize.")
        if len(text) > 1000:
            return error("TEXT_TOO_LONG", "TTS text must contain at most 1000 characters.")
        if speaker not in self.voices:
            return error(
                "INVALID_SPEAKER",
                "Choose speaker1, speaker2, or speaker3.",
                allowed_speakers=list(SPEAKERS),
            )

        output = Path(output_path).expanduser().resolve()
        current = Path(current_path).expanduser().resolve()
        result_file = Path(json_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        current.parent.mkdir(parents=True, exist_ok=True)
        result_file.parent.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [
                    self.executable,
                    "-v", self.voices[speaker],
                    "-w", str(output),
                    text.strip(),
                ],
                check=False,
                timeout=120.0,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return error("SYNTHESIS_TIMEOUT", "Speech generation timed out.")
        except OSError as exc:
            return error("SYNTHESIS_FAILED", str(exc))
        if completed.returncode != 0:
            return error(
                "SYNTHESIS_FAILED",
                (completed.stderr or "eSpeak-NG failed.").strip(),
            )
        if not output.is_file() or output.stat().st_size == 0:
            return error("SYNTHESIS_FAILED", "The engine produced no WAV file.")
        if output != current:
            shutil.copy2(output, current)
        duration = None
        try:
            with wave.open(str(output), "rb") as wav_file:
                duration = wav_file.getnframes() / float(wav_file.getframerate())
        except (OSError, wave.Error, ZeroDivisionError):
            pass
        result = {
            "ok": True,
            "error_code": "OK",
            "text": text.strip(),
            "language": self.language,
            "model_name": self.model_key,
            "engine": "espeak-ng",
            "speaker": speaker,
            "voice": self.voices[speaker],
            "audio_file": str(output),
            "current_audio": str(current),
            "audio_duration_sec": duration,
            "synthesis_sec": time.perf_counter() - started,
            "json_result": str(result_file),
        }
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
