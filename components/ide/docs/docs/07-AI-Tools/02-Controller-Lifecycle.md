# AI Controller and Lifecycle

## Constructor

```python
ai = CodyNickAI(
    workspace=None,
    camera_index=0,
    yolo_python=None,
    yolo_model=None,
    ocr_python=None,
    tesseract_model_root=None,
    stt_python=None,
    vosk_model_root=None,
    tts_python=None,
    load_timeout=120.0,
    request_timeout=120.0,
)
```

| Parameter | Purpose |
| --- | --- |
| `workspace` | Root containing `images`, `audio`, and `logs`; defaults to the current student's home |
| `camera_index` | Numeric `/dev/videoN` camera index |
| `*_python` | Advanced override for a managed AI environment interpreter |
| `yolo_model` | Advanced override for the nano YOLO model; sibling small/medium paths are inferred |
| `tesseract_model_root` | Advanced OCR data-root override |
| `vosk_model_root` | Advanced speech-model-root override |
| `load_timeout` | Maximum worker startup time in seconds |
| `request_timeout` | Maximum ordinary worker request time in seconds |

Installed examples use `workspace="/home/client"`. Leave model/runtime overrides unset
unless maintaining a custom installation.

## Properties

```python
ai.active_app          # "yolo", "ocr", "stt", "tts", or None
ai.active_model        # normalized model key or None
ai.camera_is_open      # bool
ai.listening_is_active # bool
```

## One active worker

One controller runs at most one model worker. Loading a different app or model unloads
the previous worker. The camera is separate and may be open while a worker runs.

```python
status = ai.load_app("yolo", model="nano")
ai.unload_app()
ai.close()
```

`unload_app()` stops only the AI worker. `close()` releases the camera and unloads the
worker. Repeated cleanup calls are safe.

## Recommended context manager

```python
with CodyNickAI(workspace="/home/client") as ai:
    ai.load_app("yolo", model="nano")
    result = ai.detect_objects("photo")
```

The context manager calls `close()` even when an exception occurs. For programs that
also use CodyNick gadgets, place both cleanup calls in `finally`.

