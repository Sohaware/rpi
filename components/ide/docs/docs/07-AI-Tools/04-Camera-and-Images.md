# Camera and Image Storage

## `open_camera()`

```python
status = ai.open_camera(
    width=1280,
    height=720,
    fps=30,
    use_mjpeg=True,
    warmup_seconds=3.0,
    warmup_frames=15,
)
```

Opens `camera_index`, requests the resolution/frame rate, and drains warm-up frames.
Returns camera index, measured warm-up, valid frame count, actual dimensions, FPS, and
format. If already open, returns `{"already_open": True, "camera_index": ...}`.

## `take_picture()`

```python
path = ai.take_picture(
    name=None,
    warmup_seconds=3.0,
    warmup_frames=15,
    capture_mode="brightest",
    burst_frames=12,
    cody=None,
    get_ready_sound=False,
    keep_open=False,
)
```

| Parameter | Meaning |
| --- | --- |
| `name` | Stable saved name without a path; `.jpg` is optional |
| `warmup_seconds`, `warmup_frames` | Used when the camera must first be opened |
| `capture_mode` | `brightest`, `sharpest`, or `last` |
| `burst_frames` | Candidate count for `sharpest` mode |
| `cody` | Existing `CodyNick.CN()` used for camera sounds |
| `get_ready_sound` | Play CodyJoy countdown/cue and shutter feedback |
| `keep_open` | Keep device open for a later capture; default is immediate release |

Every capture updates `/home/client/images/current.jpg`. A provided name also creates
`/home/client/images/<name>.jpg`, replacing the previous file with that name. The
method returns the saved absolute path and raises `CameraNotAvailableError` if opening,
reading, or saving fails.

For repeated captures:

```python
try:
    for number in range(5):
        ai.take_picture("sequence", keep_open=True)
finally:
    ai.close_camera()
```

## Image storage methods

```python
ai.close_camera()              # -> None
ai.save_picture("copy")        # current.jpg -> copy.jpg; returns path
ai.list_pictures()             # -> sorted list of names without .jpg
ai.picture_exists("copy")      # -> bool; None means current
ai.delete_picture("copy")      # -> None
```

Names may contain letters, digits, underscores, and hyphens only. Do not include a
folder path. Results from object detection and OCR are saved under `images/results`.

