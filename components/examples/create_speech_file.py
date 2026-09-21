"""CodyNick 0.6.0 demo: generate one named offline speech file once."""
from codynick_ai import CodyNickAI


AUDIO_NAME = "welcome_message"
TEXT = "Welcome to CodyNick. Your saved audio message is ready."


def main():
    ai = CodyNickAI(workspace="/home/client")
    try:
        if ai.audio_exists(AUDIO_NAME):
            print(f"Audio already exists: {AUDIO_NAME}.wav", flush=True)
            print("Delete it from Audio before generating it again.", flush=True)
            return
        loaded = ai.load_app("tts", model="fast", language="en")
        if not loaded.get("ok"):
            raise RuntimeError(loaded.get("message", "TTS model failed to load"))
        result = ai.tts(TEXT, AUDIO_NAME, speaker="speaker1")
        if not result.get("ok"):
            raise RuntimeError(result.get("message", "Speech generation failed"))
        print("Saved audio:", result["audio_file"], flush=True)
        print("Open Audio in the IDE to preview it.", flush=True)
    finally:
        ai.close()


if __name__ == "__main__":
    main()
