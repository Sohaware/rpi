"""Student-friendly exceptions raised by the VHL controller."""


class CodyNickAIError(RuntimeError):
    """Base class for CodyNick AI errors."""


class AppLoadError(CodyNickAIError):
    """The requested application could not be loaded."""


class AppNotLoadedError(CodyNickAIError):
    """A VHL method was called without its required application."""


class WorkerCrashedError(CodyNickAIError):
    """The active application worker stopped or returned an error."""


class CameraNotAvailableError(CodyNickAIError):
    """The configured camera could not capture an image."""


class NoImageError(CodyNickAIError):
    """An operation requires a current picture, but none exists."""


class PictureNameError(CodyNickAIError):
    """A picture name contains unsupported characters."""


class PictureNotFoundError(CodyNickAIError):
    """A requested saved picture does not exist."""


class NoAudioError(CodyNickAIError):
    """An operation requires current audio, but none exists."""


class AudioNameError(CodyNickAIError):
    """An audio name contains unsupported characters or an extension."""


class AudioNotFoundError(CodyNickAIError):
    """A requested saved audio file does not exist."""
