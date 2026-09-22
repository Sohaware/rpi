# Installed AI Tools

All currently supported models run locally after installation. Internet access is not
required to execute them.

| Feature | App/model | Example |
| --- | --- | --- |
| Object detection | YOLO nano, small, medium | `camera_objects.py` |
| Model timing comparison | YOLO models | `model_comparison.py` |
| English OCR | Tesseract standard | `camera_read_text.py` |
| Joystick OCR result | OCR plus RGB matrix | `joystick_ocr_led.py` |
| English speech-to-text | Vosk small | `voice_led_colors.py` |
| English text-to-speech | Coqui fast voice | `create_speech_file.py` |
| Saved audio playback | ALSA playback | `play_saved_audio.py` |

Only one worker application is active in a `CodyNickAI` controller at a time. Call
`load_app()` before an AI operation and `ai.close()` in `finally`.

Face detection, face recognition, age/race estimation, and chapter 8 workflows are
not part of this release.

