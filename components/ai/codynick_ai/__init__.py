"""Very-high-level CodyNick AI API."""

__release__ = "Rev.B2"

from .exceptions import (
    AppLoadError,
    AppNotLoadedError,
    AudioNameError,
    AudioNotFoundError,
    CameraNotAvailableError,
    CodyNickAIError,
    NoImageError,
    NoAudioError,
    PictureNameError,
    PictureNotFoundError,
    WorkerCrashedError,
)


def __getattr__(name):
    """Keep worker-only environments free from controller dependencies."""
    if name == "CodyNickAI":
        from .controller import CodyNickAI

        return CodyNickAI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "__release__",
    "CodyNickAI",
    "CodyNickAIError",
    "AppLoadError",
    "AppNotLoadedError",
    "AudioNameError",
    "AudioNotFoundError",
    "CameraNotAvailableError",
    "NoImageError",
    "NoAudioError",
    "PictureNameError",
    "PictureNotFoundError",
    "WorkerCrashedError",
]
