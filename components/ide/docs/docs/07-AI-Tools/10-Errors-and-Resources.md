# AI Errors, Results, and Resource Use

## Exception classes

```python
from codynick_ai import (
    CodyNickAIError,
    AppLoadError,
    AppNotLoadedError,
    WorkerCrashedError,
    CameraNotAvailableError,
    NoImageError,
    PictureNameError,
    PictureNotFoundError,
    NoAudioError,
    AudioNameError,
    AudioNotFoundError,
)
```

- `AppLoadError`: invalid, missing, or failed model/runtime.
- `AppNotLoadedError`: operation called before its required `load_app()`.
- `WorkerCrashedError`: worker stopped or returned an error.
- Camera/image/audio exceptions identify missing devices, files, or invalid names.
- All inherit from `CodyNickAIError`, except ordinary Python validation errors such as
  `ValueError` and `TypeError` raised before worker communication.

TTS loading, generation, and playback normally return structured `{ok, error_code,
message}` failures instead of raising. Other AI operations raise on failure.

## Output locations

| Content | Location |
| --- | --- |
| Captured images | `/home/client/images` |
| Annotated images and vision/OCR JSON | `/home/client/images/results` |
| Recordings and generated speech | `/home/client/audio` |
| STT/TTS JSON | `/home/client/audio/results` |
| Worker logs | `/home/client/logs` |

Use stable names to overwrite prior demo outputs. Output suffixes distinguish several
results derived from one input.

## Resource guidance

- Use YOLO nano for interactive work; load larger models only when needed.
- Load a model once and perform several same-type operations before unloading it.
- Only one worker application is active per controller.
- Release one-shot cameras immediately; use `keep_open=True` only inside a deliberate
  repeated-capture loop.
- Generate reusable speech once and replay the saved file.
- Always stop live listening and call `ai.close()` in `finally` or a context manager.

## Diagnostic properties

```python
print(ai.active_app, ai.active_model)
print(ai.camera_is_open, ai.listening_is_active)
```

If a webcam remains occupied after the script ends, inspect `/dev/video*` ownership as
described in the Troubleshooting section.
