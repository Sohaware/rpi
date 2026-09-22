# Speech, Voice Commands, and Audio

The speech-to-text example listens through a USB or webcam microphone and matches a
small vocabulary of LED color commands. It runs offline after loading the Vosk model.

Text-to-speech creates a WAV file with the installed English voice:

```python
from codynick_ai import CodyNickAI

ai = CodyNickAI(workspace="/home/client")
try:
    ai.load_app("tts", model="fast", language="en")
    result = ai.tts("Welcome to CodyNick", "welcome_message",
                    speaker="speaker1")
    print(result["audio_file"])
finally:
    ai.close()
```

Generate frequently used messages once and keep their named WAV files. A later program
can call `ai.speak("welcome_message")` without loading the text-to-speech model again.
This starts faster and avoids unnecessary generation work.

