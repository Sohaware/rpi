"""CodyNick 0.6.0 demo: play a saved audio file without loading TTS."""
from codynick_ai import CodyNickAI


AUDIO_NAME = "welcome_message"


def main():
    ai = CodyNickAI(workspace="/home/client")
    try:
        if not ai.audio_exists(AUDIO_NAME):
            raise RuntimeError(
                "welcome_message.wav is missing. Run create_speech_file.py first."
            )
        result = ai.speak(AUDIO_NAME)
        if not result.get("ok"):
            raise RuntimeError(result.get("message", "Audio playback failed"))
        print("Played:", result["audio_file"], flush=True)
    finally:
        ai.close()


if __name__ == "__main__":
    main()
