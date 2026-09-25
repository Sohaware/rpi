"""Generate the prerecorded answers used by voice_conversation.py."""
from pathlib import Path
import shutil

from codynick_ai import CodyNickAI


WORKSPACE = Path("/home/client")
ANSWER_FOLDER = WORKSPACE / "audio" / "conversation_answers"
STAGING_FOLDER = WORKSPACE / "audio" / ".conversation_answers_new"

ANSWERS = {
    "ready": [
        ";;;I am listening.",
        ";;;Yes, what would you like to ask?",
        ";;;I am ready. Please ask your question.",
    ],
    "greeting": [
        ";;;Hello! How are you today?",
        ";;;Hi there! It is nice to talk with you.",
        ";;;Hello! I hope you are having a wonderful day.",
    ],
    "identity": [
        ";;;I am your friendly learning companion.",
        ";;;I am a little assistant that can listen, speak, see, and control gadgets.",
        ";;;I am your programming and artificial intelligence companion.",
    ],
    "wellbeing": [
        ";;;I am doing great. Thank you for asking!",
        ";;;I am fine and happy to be here.",
        ";;;I am feeling wonderful and ready to help.",
    ],
    "capabilities": [
        ";;;I can listen, speak, see, and control electronic gadgets.",
        ";;;I can help you explore programming, electronics, and artificial intelligence.",
        ";;;I can recognize speech, read text, detect objects, and control colorful lights.",
    ],
    "favorite_color": [
        ";;;I like green because it looks bright and cheerful.",
        ";;;Blue is one of my favorite colors.",
        ";;;I enjoy every color in the rainbow.",
    ],
    "feelings": [
        ";;;I am happy because we are learning together.",
        ";;;Talking with you makes me feel cheerful.",
        ";;;I am feeling curious and excited today.",
    ],
    "goodbye": [
        ";;;Goodbye! It was nice talking with you.",
        ";;;See you later. Have a wonderful day!",
        ";;;Goodbye! Come back and talk with me again.",
    ],
    "not_understood": [
        ";;;I did not understand. Please try again.",
        ";;;I am sorry, I did not recognize that question.",
        ";;;Please try again with a different question.",
    ],
}


def main():
    ai = CodyNickAI(workspace=WORKSPACE)
    shutil.rmtree(STAGING_FOLDER, ignore_errors=True)
    STAGING_FOLDER.mkdir(parents=True, exist_ok=True)
    try:
        for old_playback in (WORKSPACE / "audio").glob("conversation_play_*.wav"):
            old_playback.unlink()

        loaded = ai.load_app("tts", model="fast", language="en")
        if not loaded.get("ok"):
            raise RuntimeError(loaded.get("message", "TTS model failed to load"))

        total = sum(len(items) for items in ANSWERS.values())
        completed = 0
        for topic, texts in ANSWERS.items():
            for number, text in enumerate(texts, start=1):
                name = f"conversation_{topic}_{number}"
                if ai.audio_exists(name):
                    ai.delete_audio(name)
                result = ai.tts(text, name, speaker="speaker1", volume=100)
                if not result.get("ok"):
                    raise RuntimeError(result.get("message", f"Failed to generate {name}"))
                source = Path(result["audio_file"])
                destination = STAGING_FOLDER / f"{topic}_{number}.wav"
                shutil.copy2(source, destination)
                source.unlink(missing_ok=True)
                completed += 1
                print(f"[{completed}/{total}] {destination.name}: {text}", flush=True)

        shutil.rmtree(ANSWER_FOLDER, ignore_errors=True)
        STAGING_FOLDER.replace(ANSWER_FOLDER)
        print(f"Conversation answers are ready in {ANSWER_FOLDER}", flush=True)
    finally:
        ai.close()
        shutil.rmtree(STAGING_FOLDER, ignore_errors=True)


if __name__ == "__main__":
    main()
