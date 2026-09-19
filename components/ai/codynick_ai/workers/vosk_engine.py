"""Persistent offline Vosk speech recognizer for CodyNick AI."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import wave
from datetime import datetime
from pathlib import Path

from vosk import KaldiRecognizer, Model


class VoskSpeechRecognizer:
    def __init__(self, model_path: str | Path, *, language: str, model_name: str):
        self.model_path = Path(model_path).expanduser().resolve()
        if not self.model_path.is_dir():
            raise FileNotFoundError(f"Vosk model not found: {self.model_path}")
        started = time.perf_counter()
        self.model = Model(str(self.model_path))
        self.load_seconds = time.perf_counter() - started
        self.language = language
        self.model_name = model_name

    @staticmethod
    def _validated_settings(mode, commands, min_confidence):
        mode = str(mode).strip().lower()
        if mode not in {"free", "commands"}:
            raise ValueError("mode must be 'free' or 'commands'")
        threshold = float(min_confidence)
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        cleaned = []
        if commands is not None:
            for command in commands:
                value = " ".join(str(command).strip().lower().split())
                if value and value not in cleaned:
                    cleaned.append(value)
        if mode == "commands" and not cleaned:
            raise ValueError("commands mode requires at least one command phrase")
        return mode, cleaned, threshold

    def new_recognizer(
        self,
        *,
        mode="free",
        commands=None,
        min_confidence=0.0,
        sample_rate=16000,
    ):
        mode, commands, threshold = self._validated_settings(
            mode, commands, min_confidence
        )
        if mode == "commands":
            grammar = json.dumps(commands + ["[unk]"])
            recognizer = KaldiRecognizer(self.model, float(sample_rate), grammar)
        else:
            recognizer = KaldiRecognizer(self.model, float(sample_rate))
        recognizer.SetWords(True)
        return recognizer, mode, commands, threshold

    def result_from_json(
        self,
        raw_result,
        *,
        mode,
        commands,
        min_confidence,
        event=False,
    ):
        payload = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
        text = " ".join(str(payload.get("text", "")).strip().lower().split())
        words = []
        for item in payload.get("result") or []:
            words.append(
                {
                    "word": str(item.get("word", "")),
                    "confidence": float(item.get("conf", 0.0)),
                    "start_sec": float(item.get("start", 0.0)),
                    "end_sec": float(item.get("end", 0.0)),
                }
            )
        confidence = (
            sum(item["confidence"] for item in words) / len(words) if words else 0.0
        )
        unknown = not text or "[unk]" in text
        matched = text if mode == "commands" and text in commands else None
        accepted = (
            not unknown
            and confidence >= min_confidence
            and (mode == "free" or matched is not None)
        )
        result = {
            "type": "speech" if event else "transcription",
            "text": text,
            "accepted": accepted,
            "matched_command": matched if accepted else None,
            "confidence": confidence,
            "words": words,
        }
        if event:
            result["received_at"] = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
        return result

    @staticmethod
    def _wav_is_ready(path: Path, sample_rate: int):
        try:
            with wave.open(str(path), "rb") as stream:
                return (
                    stream.getnchannels() == 1
                    and stream.getsampwidth() == 2
                    and stream.getframerate() == sample_rate
                )
        except (wave.Error, OSError):
            return False

    @staticmethod
    def _duration(path: Path):
        with wave.open(str(path), "rb") as stream:
            return stream.getnframes() / float(stream.getframerate())

    def transcribe(
        self,
        audio_path: str | Path,
        *,
        mode="free",
        commands=None,
        min_confidence=0.0,
        sample_rate=16000,
        output_dir: str | Path | None = None,
        output_suffix="stt",
        save_json=True,
    ):
        started = time.perf_counter()
        source = Path(audio_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Audio file not found: {source}")
        recognizer, mode, commands, threshold = self.new_recognizer(
            mode=mode,
            commands=commands,
            min_confidence=min_confidence,
            sample_rate=sample_rate,
        )
        conversion_started = time.perf_counter()
        conversion_performed = not self._wav_is_ready(source, sample_rate)
        with tempfile.TemporaryDirectory(prefix="codynick-stt-") as temporary:
            if conversion_performed:
                prepared = Path(temporary) / "prepared.wav"
                subprocess.run(
                    [
                        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(source), "-ac", "1", "-ar", str(sample_rate),
                        "-sample_fmt", "s16", str(prepared),
                    ],
                    check=True,
                )
            else:
                prepared = source
            conversion_seconds = time.perf_counter() - conversion_started
            audio_duration = self._duration(prepared)
            recognition_started = time.perf_counter()
            pieces = []
            with wave.open(str(prepared), "rb") as stream:
                while True:
                    data = stream.readframes(4000)
                    if not data:
                        break
                    if recognizer.AcceptWaveform(data):
                        piece = json.loads(recognizer.Result())
                        if piece.get("text"):
                            pieces.append(piece)
                final_piece = json.loads(recognizer.FinalResult())
                if final_piece.get("text"):
                    pieces.append(final_piece)
            recognition_seconds = time.perf_counter() - recognition_started

        combined_words = []
        combined_text = []
        for piece in pieces:
            combined_text.append(piece.get("text", ""))
            combined_words.extend(piece.get("result") or [])
        base = self.result_from_json(
            {"text": " ".join(combined_text), "result": combined_words},
            mode=mode,
            commands=commands,
            min_confidence=threshold,
        )
        result = {
            "audio": str(source),
            "engine": "vosk",
            "language": self.language,
            "model_name": self.model_name,
            "mode": mode,
            "commands": commands,
            **base,
            "audio_duration_sec": audio_duration,
            "sample_rate": int(sample_rate),
            "channels": 1,
            "conversion_performed": conversion_performed,
            "conversion_sec": conversion_seconds,
            "transcription_sec": recognition_seconds,
            "total_sec": time.perf_counter() - started,
            "json_result": None,
        }
        if save_json:
            destination = (
                Path(output_dir).expanduser().resolve()
                if output_dir is not None
                else source.parent
            )
            destination.mkdir(parents=True, exist_ok=True)
            output = destination / f"{source.stem}_{output_suffix}.json"
            result["json_result"] = str(output)
            output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return result
