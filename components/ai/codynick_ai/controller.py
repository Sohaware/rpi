"""Student-facing VHL controller with one persistent application worker."""

from __future__ import annotations

import atexit
import hashlib
import os
import queue
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import cv2

from .exceptions import (
    AppLoadError,
    AppNotLoadedError,
    CameraNotAvailableError,
    WorkerCrashedError,
)
from .audio_store import AudioStore
from .image_store import ImageStore
from .protocol import receive_message, send_message


YOLO_MODEL_ALIASES = {
    "n": "nano",
    "nano": "nano",
    "fast": "nano",
    "s": "small",
    "small": "small",
    "balanced": "small",
    "m": "medium",
    "medium": "medium",
    "accurate": "medium",
}

OCR_MODEL_ALIASES = {
    "fast": "fast",
    "standard": "standard",
    "normal": "standard",
    "balanced": "standard",
    "best": "best",
    "accurate": "best",
}

STT_MODEL_ALIASES = {
    "small": "small",
    "fast": "small",
    "large": "large",
    "accurate": "large",
}

STT_LANGUAGE_ALIASES = {
    "en": "en", "english": "en",
    "de": "de", "german": "de",
    "fa": "fa", "farsi": "fa", "persian": "fa",
    "ar-tn": "ar-tn", "tunisian-arabic": "ar-tn",
}

TTS_MODEL_ALIASES = {
    "default": "default",
    "fast": "en_glow",
    "glow": "en_glow",
    "glow-tts": "en_glow",
}

TTS_LANGUAGE_ALIASES = {
    "en": "en", "english": "en",
}

TTS_SPEAKERS = ("speaker1",)


def _safe_error(code: str, message: str, **details) -> dict:
    return {"ok": False, "error_code": code, "message": message, **details}


def _default_workspace() -> Path:
    configured = os.environ.get("CODYNICK_WORKSPACE")
    if configured:
        return Path(configured).expanduser().resolve()
    main_module = sys.modules.get("__main__")
    main_file = getattr(main_module, "__file__", None)
    if main_file:
        script_directory = Path(main_file).expanduser().resolve().parent
        home = Path.home().expanduser().resolve()
        # IDE source files live in ~/userfiles, but all student media must use
        # the single canonical roots ~/images and ~/audio.
        if script_directory == home / "userfiles":
            return home
        return script_directory
    return Path.cwd().resolve()


class SpeechListener:
    """Small student-facing handle for background speech events."""

    def __init__(self, controller):
        self._controller = controller

    @property
    def active(self):
        return self._controller.listening_is_active

    def get(self, timeout: float | None = 0.0):
        return self._controller._get_speech_event(timeout)

    def stop(self):
        self._controller._stop_listening()

    def __iter__(self):
        return self

    def __next__(self):
        event = self.get(timeout=None)
        if event is None:
            raise StopIteration
        return event


class CodyNickAI:
    """Very-high-level interface used directly from ``active_script.py``."""

    def __init__(
        self,
        *,
        workspace: str | Path | None = None,
        camera_index: int = 0,
        yolo_python: str | Path | None = None,
        yolo_model: str | Path | None = None,
        ocr_python: str | Path | None = None,
        tesseract_model_root: str | Path | None = None,
        stt_python: str | Path | None = None,
        vosk_model_root: str | Path | None = None,
        tts_python: str | Path | None = None,
        load_timeout: float = 120.0,
        request_timeout: float = 120.0,
    ):
        self.workspace = (
            Path(workspace).expanduser().resolve()
            if workspace is not None
            else _default_workspace()
        )
        self.camera_index = int(camera_index)
        self.image_store = ImageStore(self.workspace)
        self.audio_store = AudioStore(self.workspace)
        self.yolo_python = Path(
            yolo_python
            or os.environ.get(
                "CODYNICK_YOLO_PYTHON",
                "~/.codynick-ai/envs/yolo/bin/python",
            )
        ).expanduser().absolute()
        self.yolo_model = Path(
            yolo_model
            or os.environ.get(
                "CODYNICK_YOLO_MODEL",
                "~/.deepface/weights/yolov8n.onnx",
            )
        ).expanduser().resolve()
        weights_dir = self.yolo_model.parent
        self.yolo_models = {
            "nano": self.yolo_model,
            "small": Path(
                os.environ.get(
                    "CODYNICK_YOLO_MODEL_SMALL",
                    str(weights_dir / "yolov8s.onnx"),
                )
            ).expanduser().resolve(),
            "medium": Path(
                os.environ.get(
                    "CODYNICK_YOLO_MODEL_MEDIUM",
                    str(weights_dir / "yolov8m.onnx"),
                )
            ).expanduser().resolve(),
        }
        self.ocr_python = Path(
            ocr_python
            or os.environ.get(
                "CODYNICK_OCR_PYTHON",
                "~/.codynick-ai/envs/ocr/bin/python",
            )
        ).expanduser().absolute()
        self.tesseract_model_root = Path(
            tesseract_model_root
            or os.environ.get(
                "CODYNICK_TESSERACT_MODEL_ROOT",
                "~/.codynick-ai/models/tesseract",
            )
        ).expanduser().resolve()
        self.stt_python = Path(
            stt_python
            or os.environ.get(
                "CODYNICK_STT_PYTHON",
                "~/.codynick-ai/envs/stt/bin/python",
            )
        ).expanduser().absolute()
        self.vosk_model_root = Path(
            vosk_model_root
            or os.environ.get("CODYNICK_VOSK_MODEL_ROOT", "~/.vosk")
        ).expanduser().resolve()
        self.stt_models = {
            ("en", "small"): self.vosk_model_root / "vosk-model-small-en-us-0.15",
            ("en", "large"): self.vosk_model_root / "vosk-model-en-us-0.22-lgraph",
            ("de", "small"): self.vosk_model_root / "vosk-model-small-de-0.15",
            ("fa", "small"): self.vosk_model_root / "vosk-model-small-fa-0.42",
            ("ar-tn", "small"): self.vosk_model_root / "vosk-model-small-ar-tn-0.1-linto",
        }
        self.tts_python = Path(
            tts_python
            or os.environ.get(
                "CODYNICK_TTS_PYTHON",
                "~/.codynick-ai/envs/tts/bin/python",
            )
        ).expanduser().absolute()
        self.load_timeout = float(load_timeout)
        self.request_timeout = float(request_timeout)

        self._active_app: str | None = None
        self._active_model: str | None = None
        self._active_languages: tuple[str, ...] | None = None
        self._process: subprocess.Popen | None = None
        self._server: socket.socket | None = None
        self._connection: socket.socket | None = None
        self._stream = None
        self._runtime_dir: Path | None = None
        self._worker_log = None
        self._event_server = None
        self._event_connection = None
        self._event_stream = None
        self._event_thread = None
        self._event_stop = threading.Event()
        self._speech_events = queue.Queue(maxsize=100)
        self._listening = False
        self._request_id = 0
        self._camera = None
        self._closed = False
        atexit.register(self.close)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    @property
    def active_app(self) -> str | None:
        return self._active_app

    @property
    def active_model(self) -> str | None:
        return self._active_model

    @property
    def camera_is_open(self) -> bool:
        return self._camera is not None and self._camera.isOpened()

    @property
    def listening_is_active(self) -> bool:
        return self._active_app == "stt" and self._listening

    def open_camera(
        self,
        *,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        use_mjpeg: bool = True,
        warmup_seconds: float = 3.0,
        warmup_frames: int = 15,
    ) -> dict:
        """Open and warm the camera once for repeated captures."""
        if self.camera_is_open:
            return {"already_open": True, "camera_index": self.camera_index}

        self.close_camera()
        camera = cv2.VideoCapture(self.camera_index)
        if not camera.isOpened():
            camera.release()
            raise CameraNotAvailableError(
                f"Camera index {self.camera_index} could not be opened."
            )
        if use_mjpeg:
            camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, max(1, int(width)))
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, max(1, int(height)))
        camera.set(cv2.CAP_PROP_FPS, max(1, int(fps)))

        started_at = time.monotonic()
        deadline = started_at + max(0.0, float(warmup_seconds))
        minimum_frames = max(1, int(warmup_frames))
        frames_read = 0
        valid_frames = 0
        try:
            while time.monotonic() < deadline or frames_read < minimum_frames:
                ok, _candidate = camera.read()
                frames_read += 1
                if ok:
                    valid_frames += 1
                time.sleep(0.05)
        except Exception:
            camera.release()
            raise

        if valid_frames == 0:
            camera.release()
            raise CameraNotAvailableError(
                f"Camera index {self.camera_index} opened but returned no image."
            )

        self._camera = camera
        return {
            "already_open": False,
            "camera_index": self.camera_index,
            "warmup_sec": time.monotonic() - started_at,
            "frames_read": valid_frames,
            "width": int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": float(camera.get(cv2.CAP_PROP_FPS)),
            "format": "MJPG" if use_mjpeg else "camera-default",
        }

    def close_camera(self) -> None:
        if self._camera is not None:
            try:
                self._camera.release()
            except Exception:
                pass
        self._camera = None

    def take_picture(
        self,
        name: str | None = None,
        *,
        warmup_seconds: float = 3.0,
        warmup_frames: int = 15,
        capture_mode: str = "brightest",
        burst_frames: int = 12,
        cody: Any | None = None,
        get_ready_sound: bool = False,
        keep_open: bool = False,
    ) -> str:
        """Capture a picture, always updating ``current.jpg``.

        If ``name`` is provided, a named copy is created as well. When
        ``get_ready_sound`` is true, the supplied CodyNick connection plays a
        timed countdown, capture cue and shutter pattern during camera warm-up.
        The camera is released after capture unless ``keep_open`` is true.
        """
        capture_mode = str(capture_mode).strip().lower()
        if capture_mode not in {"brightest", "sharpest", "last"}:
            raise ValueError("capture_mode must be: brightest, sharpest, or last")
        burst_frames = max(1, int(burst_frames))

        if get_ready_sound:
            if cody is None:
                raise ValueError(
                    "get_ready_sound=True requires the existing CodyNick "
                    "connection: ai.take_picture(cody=cn, "
                    "get_ready_sound=True)"
                )
            if not hasattr(cody, "ensure_connected") or not hasattr(cody, "ser"):
                raise RuntimeError(
                    "The optional camera sound requires a CodyNick.CN() "
                    "connection supplied as cody=cn."
                )
            if not cody.ensure_connected():
                raise RuntimeError(
                    "The CodyNick chain is not connected, so the camera "
                    "get-ready sound cannot be played."
                )

        if not self.camera_is_open:
            self.open_camera(
                warmup_seconds=warmup_seconds,
                warmup_frames=warmup_frames,
            )
        camera = self._camera
        if camera is None:
            raise CameraNotAvailableError("The camera failed to remain open.")
        frame = None
        best_frame = None
        best_brightness = -1.0
        best_sharpness = -1.0
        best_score = -1.0

        def remember(candidate) -> None:
            nonlocal frame, best_frame, best_brightness, best_sharpness, best_score
            frame = candidate
            gray = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)
            brightness = float(gray.mean())
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            best_brightness = max(best_brightness, brightness)
            best_sharpness = max(best_sharpness, sharpness)
            score = (
                brightness
                if capture_mode == "brightest"
                else sharpness
                if capture_mode == "sharpest"
                else best_score + 1.0
            )
            if score > best_score:
                best_score = score
                best_frame = candidate.copy()

        try:
            # Match the legacy camera behavior: keep reading for real elapsed
            # time so USB-camera auto-exposure and white balance can settle.
            # open_camera() already performed the expensive exposure warm-up.
            # The capture cue begins immediately on every joystick-triggered
            # call while frames continue to be drained in parallel.
            warmup_duration = 0.0
            started_at = time.monotonic()
            deadline = started_at + warmup_duration
            # Three countdown beeps and an E5/G5 capture cue are followed by
            # the packaged USB-speaker shutter WAV. The buzzer shutter pattern
            # remains a fallback when that WAV is not installed.
            # Each tuple is (frequency_hz, tone_ms, following_silence_ms).
            camera_sound = (
                (700, 100, 400),
                (700, 100, 400),
                (700, 100, 400),
                (659, 60, 30),
                (784, 80, 0),
            )
            fallback_shutter = (
                (1800, 8, 18),
                (900, 22, 0),
                (250, 45, 0),
            )
            default_shutter = (
                Path(__file__).resolve().parent.parent
                / "sounds"
                / "shutter_loud.wav"
            )
            shutter_path = Path(
                os.environ.get("CODYNICK_SHUTTER_SOUND", str(default_shutter))
            ).expanduser().resolve()
            configured_shutter_device = os.environ.get("CODYNICK_AUDIO_OUTPUT")
            sound_duration = sum(
                tone_ms + silence_ms
                for _frequency, tone_ms, silence_ms in camera_sound
            ) / 1000.0
            sound_start_at = max(started_at, deadline - sound_duration)
            sound_errors: list[Exception] = []
            sound_thread: threading.Thread | None = None

            def find_usb_playback_device() -> str | None:
                """Return one currently available USB ALSA playback endpoint."""
                if configured_shutter_device:
                    return configured_shutter_device
                try:
                    listing = subprocess.run(
                        ["aplay", "-l"],
                        check=False,
                        timeout=3.0,
                        capture_output=True,
                        text=True,
                    )
                except (OSError, subprocess.SubprocessError):
                    return None
                for line in listing.stdout.splitlines():
                    if "usb" not in line.lower():
                        continue
                    match = re.search(
                        r"card\s+(\d+):.*device\s+(\d+):",
                        line,
                        re.IGNORECASE,
                    )
                    if match:
                        return f"plughw:{match.group(1)},{match.group(2)}"
                return None

            def play_buzzer_shutter() -> None:
                for frequency, tone_ms, silence_ms in fallback_shutter:
                    packet = (
                        f"CN@@BUZ@@{frequency:04d}{tone_ms:05d}"
                    ).ljust(20, "_")
                    cody.ser.send_line(packet, add_newline=False)
                    time.sleep(tone_ms / 1000.0)
                    if silence_ms:
                        time.sleep(silence_ms / 1000.0)

            def play_camera_sound() -> None:
                try:
                    for frequency, tone_ms, silence_ms in camera_sound:
                        packet = (
                            f"CN@@BUZ@@{frequency:04d}{tone_ms:05d}"
                        ).ljust(20, "_")
                        cody.ser.send_line(packet, add_newline=False)
                        time.sleep(tone_ms / 1000.0)
                        if silence_ms:
                            time.sleep(silence_ms / 1000.0)
                    shutter_device = (
                        find_usb_playback_device()
                        if shutter_path.is_file()
                        else None
                    )
                    if shutter_device is None:
                        if shutter_path.is_file():
                            print(
                                "[WARNING] USB speaker unavailable; "
                                "using the CodyJoy shutter sound."
                            )
                        play_buzzer_shutter()
                    else:
                        try:
                            subprocess.run(
                                [
                                    "aplay", "-q", "-D", shutter_device,
                                    str(shutter_path),
                                ],
                                check=True,
                                timeout=10.0,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                        except (OSError, subprocess.SubprocessError) as exc:
                            print(
                                "[WARNING] USB shutter playback failed; "
                                "using the CodyJoy shutter sound: "
                                f"{exc}"
                            )
                            play_buzzer_shutter()
                except Exception as exc:
                    sound_errors.append(exc)
                    try:
                        cody.mark_disconnected()
                    except Exception:
                        pass

            minimum_warmup_frames = 3
            discarded_frames = 0
            while (
                time.monotonic() < deadline
                or discarded_frames < minimum_warmup_frames
                or (sound_thread is not None and sound_thread.is_alive())
            ):
                now = time.monotonic()
                if (
                    get_ready_sound
                    and sound_thread is None
                    and now >= sound_start_at
                ):
                    sound_thread = threading.Thread(
                        target=play_camera_sound,
                        name="codynick-camera-sound",
                        daemon=True,
                    )
                    sound_thread.start()

                # Warm-up frames are intentionally discarded while sound runs.
                camera.read()
                discarded_frames += 1
                time.sleep(0.05)

            if get_ready_sound:
                # A zero-second warm-up can finish before normal scheduling.
                if sound_thread is None:
                    sound_thread = threading.Thread(
                        target=play_camera_sound,
                        name="codynick-camera-sound",
                        daemon=True,
                    )
                    sound_thread.start()
                sound_thread.join()
                if sound_errors:
                    raise RuntimeError(
                        "Failed to play the camera get-ready sound: "
                        f"{sound_errors[0]}"
                    ) from sound_errors[0]

            # Only post-countdown frames are candidates for the saved image.
            candidates = burst_frames if capture_mode == "sharpest" else 3
            for _ in range(candidates):
                ok, candidate = camera.read()
                if ok:
                    remember(candidate)
                time.sleep(0.02)

            # If capture failed or remained nearly black, give auto-exposure
            # one more chance and retain the brightest post-countdown frame.
            if best_frame is None or best_brightness < 3.0:
                for _ in range(20):
                    ok, candidate = camera.read()
                    if ok:
                        remember(candidate)
                    time.sleep(0.10)
        finally:
            if not keep_open:
                self.close_camera()

        if best_frame is None:
            raise CameraNotAvailableError(
                f"Camera index {self.camera_index} opened but returned no image."
            )
        frame = best_frame
        if best_brightness < 3.0:
            raise CameraNotAvailableError(
                "The camera returned only near-black frames after warm-up "
                f"(mean brightness {best_brightness:.2f}/255). Check the lens, "
                "lighting, camera index, and whether another program owns the camera."
            )

        current_path = self.image_store.path_for("current")
        if not cv2.imwrite(str(current_path), frame):
            raise CameraNotAvailableError(f"Failed to save {current_path}.")
        if name is None:
            return str(current_path)
        return str(self.image_store.save_current_as(name))

    def save_picture(self, name: str) -> str:
        return str(self.image_store.save_current_as(name))

    def list_pictures(self) -> list[str]:
        return self.image_store.list_pictures()

    def picture_exists(self, name: str | None = None) -> bool:
        return self.image_store.picture_exists(name)

    def delete_picture(self, name: str) -> None:
        self.image_store.delete_picture(name)

    @staticmethod
    def _resolve_audio_device(device: str) -> str:
        requested = str(device or "auto").strip()
        if requested not in {"auto", "webcam"}:
            return requested
        try:
            listing = subprocess.run(
                ["arecord", "-l"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(
                "Could not list microphones with arecord. Install alsa-utils."
            ) from exc
        matches = re.findall(
            r"card\s+\d+:\s+([^\s]+).*?device\s+(\d+):",
            listing,
            flags=re.IGNORECASE,
        )
        if not matches:
            raise RuntimeError("No ALSA capture microphone was found.")
        if requested == "webcam":
            preferred = [item for item in matches if "webcam" in item[0].lower()]
            if not preferred:
                raise RuntimeError("No webcam microphone was found by ALSA.")
            card, device_number = preferred[0]
        else:
            preferred = [
                item
                for item in matches
                if "webcam" in item[0].lower() or "usb" in item[0].lower()
            ]
            card, device_number = (preferred or matches)[0]
        return f"plughw:{card},{device_number}"

    def record_audio(
        self,
        name: str | None = None,
        *,
        duration: int = 5,
        device: str = "auto",
        sample_rate: int = 16000,
    ) -> str:
        """Record a mono 16-bit WAV, always updating ``audio/current.wav``."""
        seconds = int(duration)
        if seconds < 1 or seconds > 300 or float(duration) != seconds:
            raise ValueError("duration must be a whole number from 1 to 300 seconds")
        rate = int(sample_rate)
        if rate < 8000 or rate > 48000:
            raise ValueError("sample_rate must be between 8000 and 48000")
        selected_device = self._resolve_audio_device(device)
        current_path = self.audio_store.path_for("current", recording=True)
        command = [
            "arecord", "-q", "-D", selected_device,
            "-f", "S16_LE", "-r", str(rate), "-c", "1",
            "-d", str(seconds), str(current_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError("arecord is missing. Install the alsa-utils package.") from exc
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or "Audio recording failed").strip()
            raise RuntimeError(f"Audio recording failed: {message}") from exc
        if name is None:
            return str(current_path)
        return str(self.audio_store.save_current_as(name))

    def list_audio(self) -> list[str]:
        """Return saved WAV, MP3, and M4A filenames from the Audio folder."""
        return self.audio_store.list_audio()

    def audio_exists(self, name: str | None = None) -> bool:
        """Return whether a named audio file is available for playback."""
        return self.audio_store.audio_exists(name)

    def delete_audio(self, name: str) -> None:
        """Delete one named audio file from the Audio folder."""
        self.audio_store.delete_audio(name)

    def load_app(
        self,
        app: str,
        *extra,
        model: str | None = None,
        languages: list[str] | tuple[str, ...] | str | None = None,
        language: str | None = None,
        preload: list[str] | None = None,
        **options,
    ) -> dict:
        normalized = str(app).strip().lower()
        if normalized == "tts":
            if extra:
                return _safe_error(
                    "INVALID_PARAMETER",
                    "load_app('tts') accepts configuration by keyword.",
                )
            if options:
                return _safe_error(
                    "INVALID_PARAMETER",
                    "Unknown TTS load parameter(s): " + ", ".join(sorted(options)),
                )
            return self._load_tts_safe(
                model=model or "default",
                language=language or "en",
                preload=preload,
            )
        if options:
            raise TypeError(
                "Unknown load_app parameter(s): " + ", ".join(sorted(options))
            )
        if extra:
            raise TypeError("load_app() accepts configuration by keyword")
        if normalized == "stt":
            return self._load_stt(
                model=model or "small",
                language=language or "en",
                preload=preload,
            )
        if normalized == "ocr":
            return self._load_ocr(
                model=model or "fast",
                languages=languages,
                preload=preload,
            )
        if normalized != "yolo":
            raise AppLoadError(
                f"Unknown app '{app}'. Supported apps: 'yolo', 'ocr', 'stt', "
                "'tts'."
            )
        model_key = YOLO_MODEL_ALIASES.get(str(model or "nano").strip().lower())
        if model_key is None:
            choices = "nano, small, medium"
            raise AppLoadError(
                f"Unknown YOLO model '{model}'. Choose one of: {choices}."
            )
        selected_model = self.yolo_models[model_key]

        if (
            self._active_app == normalized
            and self._active_model == model_key
            and self._worker_is_running()
        ):
            status = self._request("ping", {})
            return {
                "app": normalized,
                "model_name": model_key,
                "already_loaded": True,
                **status,
            }

        self.unload_app()
        if not self.yolo_python.is_file():
            raise AppLoadError(
                f"YOLO Python interpreter not found: {self.yolo_python}. "
                "Run ./install.sh first."
            )
        if not selected_model.is_file():
            raise AppLoadError(
                f"YOLO '{model_key}' model not found: {selected_model}. "
                "Install the complete Rev.B2 model payload first."
            )

        started = time.perf_counter()
        try:
            self._runtime_dir = Path(tempfile.mkdtemp(prefix="cnai-", dir="/tmp"))
            socket_path = self._runtime_dir / "worker.sock"
            self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._server.bind(str(socket_path))
            os.chmod(socket_path, 0o600)
            self._server.listen(1)
            self._server.settimeout(0.25)

            project_root = Path(__file__).resolve().parent.parent
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = str(project_root) + (
                os.pathsep + existing_pythonpath if existing_pythonpath else ""
            )
            command = [
                str(self.yolo_python),
                "-m",
                "codynick_ai.workers.yolo_worker",
                "--socket",
                str(socket_path),
                "--model",
                str(selected_model),
                "--warmup",
            ]
            logs_dir = self.workspace / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            self._worker_log = (logs_dir / "yolo_worker.log").open(
                "a", encoding="utf-8"
            )
            self._worker_log.write(
                f"\n--- YOLO worker started {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
            )
            self._worker_log.flush()
            self._process = subprocess.Popen(
                command,
                cwd=str(project_root),
                env=environment,
                stdout=self._worker_log,
                stderr=subprocess.STDOUT,
            )

            deadline = time.monotonic() + self.load_timeout
            while self._connection is None and time.monotonic() < deadline:
                if self._process.poll() is not None:
                    raise AppLoadError(
                        f"YOLO worker exited with code {self._process.returncode} "
                        "before connecting."
                    )
                try:
                    self._connection, _ = self._server.accept()
                except socket.timeout:
                    continue
            if self._connection is None:
                raise AppLoadError("Timed out waiting for the YOLO worker to connect.")

            self._connection.settimeout(self.load_timeout)
            self._stream = self._connection.makefile("rwb")
            while True:
                message = receive_message(self._stream)
                message_type = message.get("type")
                if message_type == "loading":
                    continue
                if message_type == "ready":
                    self._active_app = normalized
                    self._active_model = model_key
                    message["model_name"] = model_key
                    message["total_load_sec"] = time.perf_counter() - started
                    message["already_loaded"] = False
                    message["preload"] = preload or []
                    return message
                if message_type == "load_error":
                    raise AppLoadError(
                        f"YOLO worker failed to load: {message.get('error_type')}: "
                        f"{message.get('message')}"
                    )
                raise AppLoadError(f"Unexpected worker startup message: {message}")
        except Exception:
            self._force_cleanup_worker()
            raise

    def _load_ocr(
        self,
        *,
        model: str,
        languages: list[str] | tuple[str, ...] | str | None,
        preload: list[str] | None,
    ) -> dict:
        if languages is None:
            requested = ["en"]
        elif isinstance(languages, str):
            requested = [languages]
        else:
            requested = list(languages)
        normalized_languages = []
        for language in requested:
            code = str(language).strip().lower().replace("-", "_")
            if not re.fullmatch(r"[a-z][a-z0-9_]*", code):
                raise AppLoadError(f"Invalid OCR language code: {language!r}")
            if code not in normalized_languages:
                normalized_languages.append(code)
        if not normalized_languages:
            raise AppLoadError("OCR requires at least one language code.")
        model_key = OCR_MODEL_ALIASES.get(str(model).strip().lower())
        if model_key is None:
            raise AppLoadError(
                f"Unknown OCR model '{model}'. Choose: fast, standard, best."
            )
        language_key = tuple(normalized_languages)

        if (
            self._active_app == "ocr"
            and self._active_languages == language_key
            and self._active_model == model_key
            and self._worker_is_running()
        ):
            status = self._request("ping", {})
            return {"already_loaded": True, **status}

        self.unload_app()
        if not self.ocr_python.is_file():
            raise AppLoadError(
                f"OCR Python interpreter not found: {self.ocr_python}. "
                "Install the OCR environment first."
            )

        started = time.perf_counter()
        try:
            self._runtime_dir = Path(tempfile.mkdtemp(prefix="cnai-", dir="/tmp"))
            socket_path = self._runtime_dir / "worker.sock"
            self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._server.bind(str(socket_path))
            os.chmod(socket_path, 0o600)
            self._server.listen(1)
            self._server.settimeout(0.25)

            project_root = Path(__file__).resolve().parent.parent
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = str(project_root) + (
                os.pathsep + existing_pythonpath if existing_pythonpath else ""
            )
            command = [
                str(self.ocr_python),
                "-m",
                "codynick_ai.workers.ocr_worker",
                "--socket",
                str(socket_path),
                "--model",
                model_key,
            ]
            if model_key != "fast":
                command.extend(
                    [
                        "--tessdata-dir",
                        str(self.tesseract_model_root / model_key),
                    ]
                )
            for language in normalized_languages:
                command.extend(["--language", language])

            logs_dir = self.workspace / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            self._worker_log = (logs_dir / "ocr_worker.log").open(
                "a", encoding="utf-8"
            )
            self._worker_log.write(
                f"\n--- OCR worker started {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
            )
            self._worker_log.flush()
            self._process = subprocess.Popen(
                command,
                cwd=str(project_root),
                env=environment,
                stdout=self._worker_log,
                stderr=subprocess.STDOUT,
            )

            deadline = time.monotonic() + self.load_timeout
            while self._connection is None and time.monotonic() < deadline:
                if self._process.poll() is not None:
                    raise AppLoadError(
                        f"OCR worker exited with code {self._process.returncode} "
                        "before connecting."
                    )
                try:
                    self._connection, _ = self._server.accept()
                except socket.timeout:
                    continue
            if self._connection is None:
                raise AppLoadError("Timed out waiting for the OCR worker to connect.")

            self._connection.settimeout(self.load_timeout)
            self._stream = self._connection.makefile("rwb")
            while True:
                message = receive_message(self._stream)
                message_type = message.get("type")
                if message_type == "loading":
                    continue
                if message_type == "ready":
                    self._active_app = "ocr"
                    self._active_model = model_key
                    self._active_languages = language_key
                    message["model_name"] = model_key
                    message["total_load_sec"] = time.perf_counter() - started
                    message["already_loaded"] = False
                    message["preload"] = preload or []
                    return message
                if message_type == "load_error":
                    raise AppLoadError(
                        f"OCR worker failed to load: {message.get('error_type')}: "
                        f"{message.get('message')}"
                    )
                raise AppLoadError(f"Unexpected OCR worker startup message: {message}")
        except Exception:
            self._force_cleanup_worker()
            raise

    def read_text(
        self,
        image: str | None = None,
        *,
        confidence: float = 0.30,
        page_mode: int = 6,
        engine_mode: int = 3,
        preprocessing: str = "none",
        perspective: str = "none",
        min_characters: int = 1,
        min_box_height: int = 0,
        allowlist: str | None = None,
        save_visual: bool = True,
        output_suffix: str = "ocr",
    ) -> dict:
        self._require_app("ocr", "read_text")
        image_path = self.image_store.path_for(image, must_exist=True)
        return self._request(
            "read",
            {
                "image_path": str(image_path),
                "confidence": float(confidence),
                "page_mode": int(page_mode),
                "engine_mode": int(engine_mode),
                "preprocessing": str(preprocessing),
                "perspective": str(perspective),
                "min_characters": int(min_characters),
                "min_box_height": int(min_box_height),
                "allowlist": allowlist,
                "save_visual": bool(save_visual),
                "output_dir": str(self.image_store.results_dir),
                "output_suffix": str(output_suffix),
            },
        )

    def _load_stt(self, *, model: str, language: str, preload: list[str] | None):
        language_key = STT_LANGUAGE_ALIASES.get(str(language).strip().lower())
        if language_key is None:
            raise AppLoadError(
                f"Unknown STT language '{language}'. Choose: en, de, fa, ar-tn."
            )
        model_key = STT_MODEL_ALIASES.get(str(model).strip().lower())
        if model_key is None:
            raise AppLoadError(
                f"Unknown STT model '{model}'. Choose: small or large."
            )
        selected_model = self.stt_models.get((language_key, model_key))
        if selected_model is None:
            raise AppLoadError(
                f"STT model '{model_key}' is not defined for language "
                f"'{language_key}'."
            )
        if (
            self._active_app == "stt"
            and self._active_model == model_key
            and self._active_languages == (language_key,)
            and self._worker_is_running()
        ):
            status = self._request("ping", {})
            return {"already_loaded": True, **status}

        self.unload_app()
        if not self.stt_python.is_file():
            raise AppLoadError(
                f"STT Python interpreter not found: {self.stt_python}. "
                "Run the Rev.B2 installer first."
            )
        if not selected_model.is_dir():
            raise AppLoadError(
                f"STT model not found: {selected_model}. Install the Vosk model payload."
            )

        started = time.perf_counter()
        try:
            self._runtime_dir = Path(tempfile.mkdtemp(prefix="cnai-", dir="/tmp"))
            socket_path = self._runtime_dir / "worker.sock"
            event_socket_path = self._runtime_dir / "events.sock"
            self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._server.bind(str(socket_path))
            os.chmod(socket_path, 0o600)
            self._server.listen(1)
            self._server.settimeout(0.25)
            self._event_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._event_server.bind(str(event_socket_path))
            os.chmod(event_socket_path, 0o600)
            self._event_server.listen(1)
            self._event_server.settimeout(0.25)

            project_root = Path(__file__).resolve().parent.parent
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = str(project_root) + (
                os.pathsep + existing_pythonpath if existing_pythonpath else ""
            )
            command = [
                str(self.stt_python), "-m", "codynick_ai.workers.stt_worker",
                "--socket", str(socket_path),
                "--events", str(event_socket_path),
                "--model-path", str(selected_model),
                "--model-name", model_key,
                "--language", language_key,
            ]
            logs_dir = self.workspace / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            self._worker_log = (logs_dir / "stt_worker.log").open(
                "a", encoding="utf-8"
            )
            self._worker_log.write(
                f"\n--- STT worker started {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
            )
            self._worker_log.flush()
            self._process = subprocess.Popen(
                command,
                cwd=str(project_root),
                env=environment,
                stdout=self._worker_log,
                stderr=subprocess.STDOUT,
            )

            deadline = time.monotonic() + self.load_timeout
            while (
                (self._connection is None or self._event_connection is None)
                and time.monotonic() < deadline
            ):
                if self._process.poll() is not None:
                    raise AppLoadError(
                        f"STT worker exited with code {self._process.returncode} "
                        "before connecting."
                    )
                if self._connection is None:
                    try:
                        self._connection, _ = self._server.accept()
                    except socket.timeout:
                        pass
                if self._event_connection is None:
                    try:
                        self._event_connection, _ = self._event_server.accept()
                    except socket.timeout:
                        pass
            if self._connection is None or self._event_connection is None:
                raise AppLoadError("Timed out waiting for the STT worker to connect.")

            self._connection.settimeout(self.load_timeout)
            self._stream = self._connection.makefile("rwb")
            self._event_stream = self._event_connection.makefile("rwb")
            self._start_event_reader()
            while True:
                message = receive_message(self._stream)
                message_type = message.get("type")
                if message_type == "loading":
                    continue
                if message_type == "ready":
                    self._active_app = "stt"
                    self._active_model = model_key
                    self._active_languages = (language_key,)
                    message["total_load_sec"] = time.perf_counter() - started
                    message["already_loaded"] = False
                    message["preload"] = preload or []
                    return message
                if message_type == "load_error":
                    raise AppLoadError(
                        f"STT worker failed to load: {message.get('error_type')}: "
                        f"{message.get('message')}"
                    )
                raise AppLoadError(f"Unexpected STT startup message: {message}")
        except Exception:
            self._force_cleanup_worker()
            raise

    def _load_tts_safe(self, *, model: str, language: str, preload) -> dict:
        """Load the original Coqui 0.22 model without exposing student errors."""
        try:
            language_key = TTS_LANGUAGE_ALIASES.get(str(language).strip().lower())
            if language_key is None:
                return _safe_error(
                    "INVALID_LANGUAGE",
                    "CodyNick 0.6.0 provides offline English TTS.",
                    allowed_languages=["en"],
                )
            model_key = TTS_MODEL_ALIASES.get(str(model).strip().lower())
            if model_key is None:
                return _safe_error(
                    "INVALID_MODEL",
                    "Choose TTS model: default or fast.",
                    allowed_models=["default", "fast"],
                )
            if model_key == "default":
                model_key = "en_glow"
            if not self.tts_python.is_file():
                return _safe_error(
                    "TTS_ENVIRONMENT_MISSING",
                    "The legacy Coqui TTS environment is not installed.",
                )
            if (
                self._active_app == "tts"
                and self._active_model == model_key
                and self._active_languages == (language_key,)
                and self._worker_is_running()
            ):
                try:
                    status = self._request("ping", {})
                except Exception as exc:
                    return _safe_error("WORKER_FAILED", str(exc))
                return {
                    "ok": True,
                    "error_code": "OK",
                    "already_loaded": True,
                    **status,
                }

            self.unload_app()
            started = time.perf_counter()
            self._runtime_dir = Path(tempfile.mkdtemp(prefix="cnai-", dir="/tmp"))
            socket_path = self._runtime_dir / "worker.sock"
            self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._server.bind(str(socket_path))
            os.chmod(socket_path, 0o600)
            self._server.listen(1)
            self._server.settimeout(0.25)

            project_root = Path(__file__).resolve().parent.parent
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = str(project_root) + (
                os.pathsep + existing_pythonpath if existing_pythonpath else ""
            )
            command = [
                str(self.tts_python), "-m", "codynick_ai.workers.tts_worker",
                "--socket", str(socket_path),
                "--model-key", model_key,
                "--language", language_key,
            ]
            logs_dir = self.workspace / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            self._worker_log = (logs_dir / "tts_worker.log").open(
                "a", encoding="utf-8"
            )
            self._worker_log.write(
                f"\n--- TTS worker started {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
            )
            self._worker_log.flush()
            self._process = subprocess.Popen(
                command,
                cwd=str(project_root),
                env=environment,
                stdout=self._worker_log,
                stderr=subprocess.STDOUT,
            )
            deadline = time.monotonic() + self.load_timeout
            while self._connection is None and time.monotonic() < deadline:
                if self._process.poll() is not None:
                    return _safe_error(
                        "MODEL_LOAD_FAILED",
                        f"TTS worker exited with code {self._process.returncode}.",
                    )
                try:
                    self._connection, _ = self._server.accept()
                except socket.timeout:
                    continue
            if self._connection is None:
                return _safe_error(
                    "MODEL_LOAD_TIMEOUT", "Timed out while loading the TTS model."
                )
            self._connection.settimeout(self.load_timeout)
            self._stream = self._connection.makefile("rwb")
            while True:
                message = receive_message(self._stream)
                message_type = message.get("type")
                if message_type == "loading":
                    continue
                if message_type == "ready":
                    self._active_app = "tts"
                    self._active_model = model_key
                    self._active_languages = (language_key,)
                    return {
                        "ok": True,
                        "error_code": "OK",
                        "already_loaded": False,
                        "total_load_sec": time.perf_counter() - started,
                        "preload": preload or [],
                        **message,
                    }
                if message_type == "load_error":
                    return _safe_error(
                        "MODEL_LOAD_FAILED",
                        message.get("message", "TTS model failed to load."),
                        error_type=message.get("error_type"),
                    )
                return _safe_error(
                    "WORKER_PROTOCOL_ERROR", "Unexpected TTS startup response."
                )
        except Exception as exc:
            return _safe_error("MODEL_LOAD_FAILED", str(exc))
        finally:
            if self._active_app != "tts" and self._process is not None:
                self._force_cleanup_worker()

    def tts(
        self,
        text: str | None = None,
        name: str | None = None,
        *extra,
        speaker: str = "speaker1",
        volume: float = 100,
        **options,
    ) -> dict:
        """Generate a named WAV; all expected errors are returned as codes."""
        if extra:
            return _safe_error(
                "INVALID_PARAMETER", "tts() accepts only text and name by position."
            )
        if options:
            return _safe_error(
                "INVALID_PARAMETER",
                "Unknown TTS parameter(s): " + ", ".join(sorted(options)),
            )
        if not isinstance(text, str) or not text.strip():
            return _safe_error("EMPTY_TEXT", "Provide some text to synthesize.")
        if len(text) > 1000:
            return _safe_error(
                "TEXT_TOO_LONG", "TTS text must contain at most 1000 characters."
            )
        if name is None or not str(name).strip():
            return _safe_error("INVALID_NAME", "Provide a name for the generated audio.")
        speaker_key = str(speaker).strip().lower()
        if speaker_key not in TTS_SPEAKERS:
            return _safe_error(
                "INVALID_SPEAKER",
                "Choose speaker1.",
                allowed_speakers=list(TTS_SPEAKERS),
            )
        try:
            volume_value = float(volume)
        except (TypeError, ValueError):
            return _safe_error("INVALID_VOLUME", "Volume must be from 0 to 300.")
        if not 0 <= volume_value <= 300:
            return _safe_error("INVALID_VOLUME", "Volume must be from 0 to 300.")
        if self._active_app != "tts" or not self._worker_is_running():
            return _safe_error(
                "APP_NOT_LOADED", "Call ai.load_app('tts') before ai.tts()."
            )
        try:
            output_path = self.audio_store.path_for(name, recording=True)
        except Exception as exc:
            return _safe_error("INVALID_NAME", str(exc))
        try:
            result = self._request(
                "synthesize",
                {
                    "text": text.strip(),
                    "speaker": speaker_key,
                    "volume": volume_value,
                    "output_path": str(output_path),
                    "current_path": str(
                        self.audio_store.path_for("current", recording=True)
                    ),
                    "json_path": str(
                        self.audio_store.results_dir / f"{output_path.stem}_tts.json"
                    ),
                },
            )
        except Exception as exc:
            return _safe_error("WORKER_FAILED", str(exc))
        return result

    @staticmethod
    def _find_playback_device(device: str = "auto") -> tuple[str | None, str | None]:
        requested = str(device or "auto").strip()
        if requested != "auto":
            return requested, None
        try:
            listing = subprocess.run(
                ["aplay", "-l"], check=False, timeout=3.0,
                capture_output=True, text=True,
            )
        except FileNotFoundError:
            return None, "APLAY_NOT_FOUND"
        except (OSError, subprocess.SubprocessError):
            return None, "PLAYBACK_DEVICE_QUERY_FAILED"
        candidates = []
        for line in listing.stdout.splitlines():
            match = re.search(
                r"card\s+(\d+):.*device\s+(\d+):", line, re.IGNORECASE
            )
            if match:
                candidates.append(("usb" in line.lower(), match.groups()))
        if not candidates:
            return None, "NO_PLAYBACK_DEVICE"
        candidates.sort(key=lambda item: item[0], reverse=True)
        card, output = candidates[0][1]
        return f"plughw:{card},{output}", None

    def speak(
        self,
        name: str | None = None,
        *extra,
        device: str = "auto",
        volume: float = 100,
        **options,
    ) -> dict:
        """Play an existing audio file once without loading or running TTS."""
        if extra:
            return _safe_error(
                "INVALID_PARAMETER", "speak() accepts only the audio name by position."
            )
        if options:
            return _safe_error(
                "INVALID_PARAMETER",
                "Unknown playback parameter(s): " + ", ".join(sorted(options)),
            )
        try:
            volume_value = float(volume)
        except (TypeError, ValueError):
            return _safe_error("INVALID_VOLUME", "Volume must be from 0 to 300.")
        if not 0 <= volume_value <= 300:
            return _safe_error("INVALID_VOLUME", "Volume must be from 0 to 300.")
        try:
            audio_path = self.audio_store.path_for(name, must_exist=True)
        except Exception as exc:
            return _safe_error("AUDIO_NOT_FOUND", str(exc))
        selected_device, error_code = self._find_playback_device(device)
        if selected_device is None:
            messages = {
                "APLAY_NOT_FOUND": "aplay is not installed.",
                "PLAYBACK_DEVICE_QUERY_FAILED": "Could not inspect audio outputs.",
                "NO_PLAYBACK_DEVICE": "No ALSA playback device is available.",
            }
            return _safe_error(
                error_code or "NO_PLAYBACK_DEVICE",
                messages.get(error_code, "No playback device is available."),
                audio_file=str(audio_path),
            )
        started = time.perf_counter()
        cache_dir = self.workspace / ".cache" / "codynick" / "audio"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = hashlib.sha256(
            f"{audio_path}:{volume_value:.4f}".encode("utf-8")
        ).hexdigest()[:20]
        converted_path = cache_dir / f"{cache_key}.wav"
        cache_reused = (
            converted_path.is_file()
            and converted_path.stat().st_size > 0
            and converted_path.stat().st_mtime_ns >= audio_path.stat().st_mtime_ns
        )
        try:
            if not cache_reused:
                converted = subprocess.run(
                    [
                        "ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(audio_path),
                        "-af", f"volume={volume_value / 100.0:.4f}",
                        "-ar", "48000", "-ac", "2",
                        str(converted_path),
                    ],
                    check=False,
                    timeout=120.0,
                    capture_output=True,
                    text=True,
                )
                if converted.returncode != 0:
                    converted_path.unlink(missing_ok=True)
                    return _safe_error(
                        "AUDIO_CONVERSION_FAILED",
                        (converted.stderr or "Audio conversion failed.").strip(),
                    )
            played = subprocess.run(
                ["aplay", "-q", "-D", selected_device, str(converted_path)],
                check=False,
                timeout=300.0,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return _safe_error("PLAYBACK_TIMEOUT", "Audio playback timed out.")
        except OSError as exc:
            return _safe_error("PLAYBACK_FAILED", str(exc))
        if played.returncode != 0:
            return _safe_error(
                "PLAYBACK_FAILED",
                (played.stderr or "Audio playback failed.").strip(),
                audio_file=str(audio_path),
                device=selected_device,
            )
        return {
            "ok": True,
            "error_code": "OK",
            "audio_file": str(audio_path),
            "playback_file": str(converted_path),
            "playback_cache_reused": cache_reused,
            "device": selected_device,
            "volume": volume_value,
            "playback_sec": time.perf_counter() - started,
        }

    def transcribe(
        self,
        audio: str | None = None,
        *,
        mode: str = "free",
        commands: list[str] | tuple[str, ...] | None = None,
        min_confidence: float = 0.0,
        output_suffix: str = "stt",
        save_json: bool = True,
    ) -> dict:
        self._require_app("stt", "transcribe")
        audio_path = self.audio_store.path_for(audio, must_exist=True)
        return self._request(
            "transcribe",
            {
                "audio_path": str(audio_path),
                "mode": str(mode),
                "commands": list(commands) if commands is not None else None,
                "min_confidence": float(min_confidence),
                "output_dir": str(self.audio_store.results_dir),
                "output_suffix": str(output_suffix),
                "save_json": bool(save_json),
            },
        )

    def listen(
        self,
        *,
        commands: list[str] | tuple[str, ...] | None = None,
        min_confidence: float = 0.0,
        device: str = "auto",
    ) -> SpeechListener:
        """Start background listening and return a simple event handle."""
        self._require_app("stt", "listen")
        mode = "commands" if commands else "free"
        selected_device = self._resolve_audio_device(device)
        while True:
            try:
                self._speech_events.get_nowait()
            except queue.Empty:
                break
        self._request(
            "start_listening",
            {
                "mode": mode,
                "commands": list(commands) if commands else None,
                "min_confidence": float(min_confidence),
                "device": selected_device,
                "sample_rate": 16000,
            },
        )
        self._listening = True
        return SpeechListener(self)

    def detect_objects(
        self,
        image: str | None = None,
        *,
        confidence: float = 0.35,
        iou: float = 0.5,
        save_visual: bool = True,
        output_suffix: str = "objects",
    ) -> dict:
        self._require_app("yolo", "detect_objects")
        image_path = self.image_store.path_for(image, must_exist=True)
        return self._request(
            "detect",
            {
                "image_path": str(image_path),
                "conf_threshold": float(confidence),
                "iou_threshold": float(iou),
                "save_visual": bool(save_visual),
                "output_dir": str(self.image_store.results_dir),
                "output_suffix": str(output_suffix),
            },
        )

    def unload_app(self) -> None:
        if self._process is None:
            self._active_app = None
            self._active_model = None
            self._active_languages = None
            self._listening = False
            return
        if self._worker_is_running() and self._stream is not None:
            try:
                self._request("shutdown", {}, timeout=5.0)
            except Exception:
                pass
        if self._process.poll() is None:
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self._process.terminate()
                try:
                    self._process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=3.0)
        self._force_cleanup_worker()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.close_camera()
        self.unload_app()

    def _start_event_reader(self) -> None:
        self._event_stop.clear()

        def read_events():
            while not self._event_stop.is_set() and self._event_stream is not None:
                try:
                    event = receive_message(self._event_stream)
                except (EOFError, OSError, ValueError):
                    break
                try:
                    self._speech_events.put_nowait(event)
                except queue.Full:
                    try:
                        self._speech_events.get_nowait()
                    except queue.Empty:
                        pass
                    self._speech_events.put_nowait(event)

        self._event_thread = threading.Thread(
            target=read_events,
            name="codynick-stt-events",
            daemon=True,
        )
        self._event_thread.start()

    def _get_speech_event(self, timeout: float | None):
        try:
            if timeout is None:
                event = self._speech_events.get()
            else:
                wait = max(0.0, float(timeout))
                event = self._speech_events.get(timeout=wait) if wait else (
                    self._speech_events.get_nowait()
                )
        except queue.Empty:
            return None
        if event.get("type") == "speech_error":
            self._listening = False
            raise WorkerCrashedError(
                f"Live speech recognition failed: {event.get('message', 'unknown error')}"
            )
        return event

    def _stop_listening(self) -> None:
        if self._active_app == "stt" and self._worker_is_running() and self._listening:
            self._request("stop_listening", {}, timeout=10.0)
        self._listening = False

    def _require_app(self, required: str, method: str) -> None:
        if self._active_app != required or not self._worker_is_running():
            loaded = self._active_app or "none"
            raise AppNotLoadedError(
                f"{method}() requires app '{required}', but app '{loaded}' is "
                f"loaded. Call ai.load_app('{required}') first."
            )

    def _worker_is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _request(
        self,
        command: str,
        arguments: dict[str, Any],
        *,
        timeout: float | None = None,
    ):
        if not self._worker_is_running() or self._stream is None:
            raise WorkerCrashedError("The active application worker is not running.")
        self._request_id += 1
        request_id = self._request_id
        if self._connection is not None:
            self._connection.settimeout(timeout or self.request_timeout)
        try:
            send_message(
                self._stream,
                {"id": request_id, "command": command, "arguments": arguments},
            )
            response = receive_message(self._stream)
        except (EOFError, OSError, TimeoutError) as exc:
            raise WorkerCrashedError(
                f"The '{self._active_app}' worker stopped responding: {exc}"
            ) from exc
        if response.get("id") != request_id:
            raise WorkerCrashedError(
                f"Worker response ID mismatch: expected {request_id}, "
                f"received {response.get('id')}."
            )
        if not response.get("ok"):
            raise WorkerCrashedError(
                f"{response.get('error_type', 'WorkerError')}: "
                f"{response.get('message', 'Unknown worker error')}"
            )
        return response.get("result")

    def _force_cleanup_worker(self) -> None:
        self._event_stop.set()
        for resource in (
            self._event_stream,
            self._event_connection,
            self._event_server,
            self._stream,
            self._connection,
            self._server,
        ):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    pass
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2.0)
        if self._runtime_dir is not None:
            shutil.rmtree(self._runtime_dir, ignore_errors=True)
        if self._worker_log is not None:
            try:
                self._worker_log.close()
            except Exception:
                pass
        if self._event_thread is not None and self._event_thread.is_alive():
            self._event_thread.join(timeout=1.0)
        self._active_app = None
        self._active_model = None
        self._active_languages = None
        self._process = None
        self._server = None
        self._connection = None
        self._stream = None
        self._runtime_dir = None
        self._worker_log = None
        self._event_server = None
        self._event_connection = None
        self._event_stream = None
        self._event_thread = None
        self._listening = False
