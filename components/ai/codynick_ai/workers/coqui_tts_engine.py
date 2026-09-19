"""Original CodyNick Coqui TTS 0.22 engine, wrapped for the Rev.B2 API."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import wave
from pathlib import Path

from TTS.api import TTS


MODELS = {
    "en_glow": {
        "name": "tts_models/en/ljspeech/glow-tts",
        "language": "en",
        "speakers": {"speaker1": None},
    },
    "en_vits": {
        "name": "tts_models/en/ljspeech/vits",
        "language": "en",
        "speakers": {"speaker1": None},
    },
    "en_vctk": {
        "name": "tts_models/en/vctk/vits",
        "language": "en",
        "speakers": {
            "speaker1": "p225",
            "speaker2": "p231",
            "speaker3": "p240",
        },
    },
    "fr_vits": {
        "name": "tts_models/fr/css10/vits",
        "language": "fr",
        "speakers": {"speaker1": None},
    },
}


def error(code: str, message: str, **details) -> dict:
    return {"ok": False, "error_code": code, "message": message, **details}


class CoquiTtsEngine:
    def __init__(self, model_key: str, language: str):
        started = time.perf_counter()
        if model_key not in MODELS:
            raise ValueError(f"Unknown legacy TTS model: {model_key}")
        config = MODELS[model_key]
        if config["language"] != language:
            raise ValueError("The selected model and language do not match.")
        self.model_key = model_key
        self.model_name = config["name"]
        self.language = language
        self.voices = config["speakers"]
        self.tts = TTS(model_name=self.model_name, progress_bar=False, gpu=False)
        self.load_seconds = time.perf_counter() - started

    def synthesize(
        self, *, text, speaker, volume, output_path, current_path, json_path
    ):
        if speaker not in self.voices:
            return error(
                "INVALID_SPEAKER",
                "This legacy model does not provide that speaker.",
                allowed_speakers=list(self.voices),
            )
        output = Path(output_path).expanduser().resolve()
        current = Path(current_path).expanduser().resolve()
        result_file = Path(json_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        current.parent.mkdir(parents=True, exist_ok=True)
        result_file.parent.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        try:
            self.tts.tts_to_file(
                text=text,
                file_path=str(output),
                speaker=self.voices[speaker],
                language=None,
            )
        except Exception as exc:
            return error("SYNTHESIS_FAILED", str(exc))
        if not output.is_file() or output.stat().st_size == 0:
            return error("SYNTHESIS_FAILED", "Coqui produced no WAV file.")
        if volume != 100:
            adjusted = output.with_name(output.stem + ".volume-adjusted.wav")
            try:
                converted = subprocess.run(
                    [
                        "ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(output),
                        "-af", f"volume={volume / 100.0:.4f}",
                        str(adjusted),
                    ],
                    check=False,
                    timeout=120.0,
                    capture_output=True,
                    text=True,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                return error("VOLUME_ADJUSTMENT_FAILED", str(exc))
            if converted.returncode != 0 or not adjusted.is_file():
                return error(
                    "VOLUME_ADJUSTMENT_FAILED",
                    (converted.stderr or "Volume adjustment failed.").strip(),
                )
            adjusted.replace(output)
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
            "text": text,
            "language": self.language,
            "model_name": self.model_key,
            "coqui_model_name": self.model_name,
            "engine": "Coqui TTS 0.22.0",
            "speaker": speaker,
            "volume": volume,
            "coqui_speaker": self.voices[speaker],
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
