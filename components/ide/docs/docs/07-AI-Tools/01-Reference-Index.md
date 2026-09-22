# CodyNick AI Reference

Import the high-level controller:

```python
from codynick_ai import CodyNickAI
```

## Lifecycle

```python
ai = CodyNickAI(...)
ai.load_app(...)
ai.unload_app()
ai.close()
```

## Camera and images

```python
ai.open_camera(...)
ai.take_picture(...)
ai.close_camera()
ai.save_picture(name)
ai.list_pictures()
ai.picture_exists(name)
ai.delete_picture(name)
```

## Audio

```python
ai.record_audio(...)
ai.list_audio()
ai.audio_exists(name)
ai.delete_audio(name)
ai.speak(name, ...)
```

## AI operations

```python
ai.detect_objects(...)
ai.read_text(...)
ai.transcribe(...)
ai.listen(...)
ai.tts(...)
```

The installed release supports USB-camera YOLO, English OCR, offline English STT and
voice commands, offline English TTS, and saved-audio playback. Face analysis, age/race
estimation, and chapter 8 workflows are not installed.

