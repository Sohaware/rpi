# Live Voice Commands

Load STT, then start a background listener:

```python
ai.load_app("stt", model="small", language="en")
listener = ai.listen(
    commands=["red", "green", "blue", "lights off"],
    min_confidence=0.60,
    device="auto",
)
```

## `listen()` parameters

- A non-empty `commands` sequence enables command mode; `None` enables free speech.
- `min_confidence` is the minimum average word confidence from `0.0` to `1.0`.
- `device` follows the same rules as `record_audio()`.
- The method returns a `SpeechListener` and starts 16 kHz capture in the worker.

## Consuming events

```python
try:
    for event in listener:
        print(event["text"], event["confidence"])
        if not event["accepted"]:
            continue
        command = event["matched_command"]
        if command == "lights off":
            break
finally:
    listener.stop()
```

An event contains:

```python
{
    "type": "speech",
    "text": "green",
    "accepted": True,
    "matched_command": "green",
    "confidence": 0.91,
    "words": [...],
    "received_at": "ISO timestamp",
}
```

Other listener operations:

```python
listener.active                 # bool
event = listener.get(timeout=1) # event or None
listener.stop()                 # stop microphone capture
```

Iteration waits for events until stopped. Always call `stop()` in `finally`; `ai.close()`
also stops listening while unloading the STT worker.

