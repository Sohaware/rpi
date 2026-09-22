# Text-to-Speech and Playback

## Generate a named WAV

```python
status = ai.load_app("tts", model="fast", language="en")
if status["ok"]:
    result = ai.tts(
        "Welcome to CodyNick",
        "welcome_message",
        speaker="speaker1",
        volume=100,
    )
```

## `tts()`

```python
result = ai.tts(text, name, speaker="speaker1", volume=100)
```

- `text` must contain 1 to 1000 characters.
- `name` is required and follows audio naming rules.
- The installed voice is `speaker1`.
- `volume` is `0..300`, where `100` is the original level.
- TTS must already be loaded.

Success returns `ok=True`, `error_code="OK"`, `audio_file`, `current_audio`,
`audio_duration_sec`, `synthesis_sec`, `speaker`, `volume`, and `json_result`.
Expected failures return `ok=False`, `error_code`, and `message`; check `ok` rather
than wrapping ordinary validation failures in `try/except`.

## Play an existing file

```python
result = ai.speak(
    "welcome_message",
    device="auto",
    volume=100,
)
```

`speak()` does not require the TTS worker. It accepts WAV, MP3, or M4A, converts and
caches a 48 kHz stereo WAV for the requested volume, then plays it through ALSA.
`device="auto"` prefers USB output; an explicit ALSA device is accepted.

Success keys include `audio_file`, `playback_file`, `playback_cache_reused`, `device`,
`volume`, and `playback_sec`. Failures use error codes such as `AUDIO_NOT_FOUND`,
`NO_PLAYBACK_DEVICE`, `AUDIO_CONVERSION_FAILED`, `PLAYBACK_TIMEOUT`, or
`PLAYBACK_FAILED`.

Generate reusable messages once, then call `speak()` in later programs without loading
the large TTS model.

