# Audio Recording and Speech-to-Text

## `record_audio()`

```python
path = ai.record_audio(
    name=None,
    duration=5,
    device="auto",
    sample_rate=16000,
)
```

Records mono 16-bit WAV. `duration` must be a whole number from 1 to 300 seconds;
`sample_rate` must be 8000 to 48000. `device="auto"` prefers a webcam or USB capture
device; `device="webcam"` requires a webcam-named ALSA input. An explicit ALSA device
such as `plughw:CARD,DEVICE` is also accepted.

Every recording updates `audio/current.wav`. A name creates a persistent named WAV and
the method returns its absolute path.

## Audio storage

```python
ai.list_audio()            # WAV, MP3, and M4A filenames including extensions
ai.audio_exists("sample")  # -> bool
ai.delete_audio("sample")  # -> None
```

Names allow letters, digits, underscores, and hyphens. A `.wav`, `.mp3`, or `.m4a`
extension may be supplied, but no path is allowed.

## `transcribe()`

```python
ai.load_app("stt", model="small", language="en")
result = ai.transcribe(
    audio=None,
    mode="free",
    commands=None,
    min_confidence=0.0,
    output_suffix="stt",
    save_json=True,
)
```

- `audio=None` selects the current recording.
- `mode` is `free` or `commands`.
- In command mode, `commands` is the accepted phrase list.
- `min_confidence` is `0.0..1.0`.
- JSON results are stored under `audio/results`.

Important result keys:

```python
result["text"]
result["accepted"]
result["matched_command"]
result["confidence"]
result["words"]  # word, confidence, start_sec, end_sec
result["audio_duration_sec"]
result["transcription_sec"]
result["json_result"]
```

In command mode, `accepted` requires recognized text to exactly match a normalized
command and meet the confidence threshold.

