"""Offline wake-phrase conversation with prerecorded answers and CodyJoy feedback."""
from pathlib import Path
import random
import shutil
import time

import CodyNick
from codynick_ai import CodyNickAI


WORKSPACE = Path("/home/client")
ANSWER_FOLDER = WORKSPACE / "audio" / "conversation_answers"
PLAYBACK_PREFIX = "conversation_play_"
WAKE_PHRASES = ["wake up", "please wake up"]
QUESTION_TIMEOUT = 10.0
MIN_CONFIDENCE = 0.45

QUESTION_TOPICS = {
    "hello": "greeting",
    "hi": "greeting",
    "good morning": "greeting",
    "good afternoon": "greeting",
    "good evening": "greeting",
    "good night": "greeting",
    "what is your name": "identity",
    "who are you": "identity",
    "tell me about yourself": "identity",
    "how are you": "wellbeing",
    "how are you today": "wellbeing",
    "are you okay": "wellbeing",
    "what can you do": "capabilities",
    "how can you help me": "capabilities",
    "what do you do": "capabilities",
    "what is your favorite color": "favorite_color",
    "which color do you like": "favorite_color",
    "do you have a favorite color": "favorite_color",
    "are you happy": "feelings",
    "how do you feel": "feelings",
    "are you sad": "feelings",
    "goodbye": "goodbye",
    "bye": "goodbye",
    "see you later": "goodbye",
    "sleep": "sleep",
    "go to sleep": "sleep",
}
QUESTION_PHRASES = list(QUESTION_TOPICS)


def set_leds(cody, leds, color):
    CodyNick.RGB_Matrix.clear(cody)
    for led in leds:
        CodyNick.RGB_Matrix.set(cody, led, color)
        time.sleep(0.002)


def waiting_effect(cody):
    set_leds(cody, [0], "#003080")


def wake_effect(cody):
    set_leds(cody, range(16), "#00FF00")
    CodyNick.CJP_Sound_Maker.play_until_done(cody, "C5", 100)
    CodyNick.CJP_Sound_Maker.play_until_done(cody, "E5", 160)


def listening_effect(cody):
    set_leds(cody, [5, 6, 9, 10], "#00FFFF")


def processing_effect(cody):
    set_leds(cody, [0, 4, 8, 12], "#FFFF00")


def answering_effect(cody):
    set_leds(cody, [0, 3, 5, 6, 9, 10, 12, 15], "#00FF00")
    CodyNick.CJP_Sound_Maker.play_until_done(cody, "G5", 100)


def not_understood_effect(cody):
    for _ in range(2):
        set_leds(cody, range(16), "#FF8000")
        time.sleep(0.12)
        CodyNick.RGB_Matrix.clear(cody)
        time.sleep(0.08)
    CodyNick.CJP_Sound_Maker.play_until_done(cody, "E5", 100)
    CodyNick.CJP_Sound_Maker.play_until_done(cody, "C5", 180)


def goodbye_effect(cody):
    set_leds(cody, range(16), "#FF00FF")
    for note in ["G5", "E5", "C5"]:
        CodyNick.CJP_Sound_Maker.play_until_done(cody, note, 130)


def choose_answer(topic, previous_answers):
    choices = sorted(ANSWER_FOLDER.glob(f"{topic}_*.wav"))
    if not choices:
        raise FileNotFoundError(f"No prerecorded answers found for: {topic}")
    previous = previous_answers.get(topic)
    available = [path for path in choices if path != previous] or choices
    selected = random.choice(available)
    previous_answers[topic] = selected
    return selected


def play_answer(ai, topic, previous_answers):
    selected = choose_answer(topic, previous_answers)
    playback_name = f"{PLAYBACK_PREFIX}{selected.stem}"
    playback_file = WORKSPACE / "audio" / f"{playback_name}.wav"
    shutil.copy2(selected, playback_file)
    result = ai.speak(playback_name, device="auto", volume=100)
    if not result.get("ok", True):
        raise RuntimeError(result.get("message", "Audio playback failed"))
    print(f"Played: {selected.name}", flush=True)


def wait_for_command(ai, commands, timeout=None, return_unmatched=False):
    listener = ai.listen(commands=commands, min_confidence=MIN_CONFIDENCE, device="auto")
    started = time.monotonic()
    try:
        while timeout is None or time.monotonic() - started < timeout:
            event = listener.get(timeout=0.25)
            if event and event.get("accepted"):
                print(
                    f"Heard: {event['matched_command']} "
                    f"(score {event.get('confidence', 0.0):.2f})",
                    flush=True,
                )
                return event["matched_command"]
            if event and return_unmatched and event.get("text"):
                print(f"Did not recognize a question: {event['text']}", flush=True)
                return "__unknown__"
        return None
    finally:
        listener.stop()


def main():
    if not ANSWER_FOLDER.is_dir():
        raise RuntimeError("Run generate_conversation_answers.py first.")

    cody = CodyNick.CN()
    ai = CodyNickAI(workspace=WORKSPACE)
    previous_answers = {}
    try:
        if not cody.ensure_connected():
            raise RuntimeError("CodyNick gadget not found. Connect it and run again.")
        print("Loading offline English speech recognition...", flush=True)
        ai.load_app("stt", model="small", language="en")
        print("Ready. Say: wake up", flush=True)

        while True:
            waiting_effect(cody)
            wait_for_command(ai, WAKE_PHRASES)

            wake_effect(cody)
            play_answer(ai, "ready", previous_answers)
            print("Conversation active. Ask questions without repeating the wake phrase.", flush=True)

            while True:
                listening_effect(cody)
                question = wait_for_command(
                    ai,
                    QUESTION_PHRASES,
                    timeout=QUESTION_TIMEOUT,
                    return_unmatched=True,
                )

                if question is None:
                    print("No speech for 10 seconds. Returning to wake mode.", flush=True)
                    break
                if question == "__unknown__":
                    not_understood_effect(cody)
                    play_answer(ai, "not_understood", previous_answers)
                    continue

                processing_effect(cody)
                topic = QUESTION_TOPICS[question]
                if topic == "sleep":
                    print("Sleep command received. Returning to wake mode.", flush=True)
                    break
                if topic == "goodbye":
                    goodbye_effect(cody)
                else:
                    answering_effect(cody)
                play_answer(ai, topic, previous_answers)
                if topic == "goodbye":
                    break
    finally:
        ai.close()
        CodyNick.RGB_Matrix.clear(cody)
        cody.close()
        for playback_file in (WORKSPACE / "audio").glob(f"{PLAYBACK_PREFIX}*.wav"):
            playback_file.unlink(missing_ok=True)
        print("Conversation stopped; microphone, speaker, and LEDs are off.", flush=True)


if __name__ == "__main__":
    main()
