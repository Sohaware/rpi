"""Named and default audio storage for student scripts."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from .exceptions import AudioNameError, AudioNotFoundError, NoAudioError


_VALID_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
_SUPPORTED_EXTENSIONS = (".wav", ".mp3", ".m4a")


class AudioStore:
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).expanduser().resolve()
        self.audio_dir = self.workspace / "audio"
        self.results_dir = self.audio_dir / "results"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def normalize_name(name: str | None) -> tuple[str, str | None]:
        if name is None or str(name).strip() == "":
            return "current", None
        value = str(name).strip()
        suffix = Path(value).suffix.lower()
        if suffix:
            if suffix not in _SUPPORTED_EXTENSIONS:
                raise AudioNameError("Audio files must be WAV, MP3, or M4A.")
            value = value[: -len(suffix)]
        if not _VALID_NAME.fullmatch(value):
            raise AudioNameError(
                "Audio names may contain only letters, numbers, underscores, "
                "and hyphens. Do not include a folder path."
            )
        return value, suffix or None

    def path_for(
        self,
        name: str | None = None,
        *,
        must_exist: bool = False,
        recording: bool = False,
    ) -> Path:
        stem, suffix = self.normalize_name(name)
        if recording:
            return self.audio_dir / f"{stem}.wav"
        if suffix:
            candidate = self.audio_dir / f"{stem}{suffix}"
            if candidate.is_file() or not must_exist:
                return candidate
        else:
            for extension in _SUPPORTED_EXTENSIONS:
                candidate = self.audio_dir / f"{stem}{extension}"
                if candidate.is_file():
                    return candidate
            candidate = self.audio_dir / f"{stem}.wav"
            if not must_exist:
                return candidate
        available = ", ".join(self.list_audio()) or "none"
        raise AudioNotFoundError(
            f"No saved audio named '{stem}'. Available audio: {available}"
        )

    def save_current_as(self, name: str) -> Path:
        source = self.path_for("current.wav")
        if not source.is_file():
            raise NoAudioError("No current audio exists. Call ai.record_audio() first.")
        destination = self.path_for(name, recording=True)
        if destination != source:
            shutil.copy2(source, destination)
        return destination

    def list_audio(self) -> list[str]:
        return sorted(
            path.name
            for path in self.audio_dir.iterdir()
            if path.is_file() and path.suffix.lower() in _SUPPORTED_EXTENSIONS
        )

    def audio_exists(self, name: str | None = None) -> bool:
        try:
            return self.path_for(name, must_exist=True).is_file()
        except AudioNotFoundError:
            return False

    def delete_audio(self, name: str) -> None:
        self.path_for(name, must_exist=True).unlink()
