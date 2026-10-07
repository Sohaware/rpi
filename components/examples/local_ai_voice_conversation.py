"""Offline voice conversation using STT, Gemma, TTS, and CodyJoy Pro feedback."""
import time

import CodyNick
from codynick_ai import CodyNickAI


WAKE_PHRASES = ["wake up"]
SLEEP_PHRASES = {"sleep", "go to sleep"}
STOP_PHRASES = {"stop listening", "goodbye"}
QUESTION_TIMEOUT = 10


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


def goodbye_effect(cody):
    set_leds(cody, range(16), "#FF00FF")
    for note in ["G5", "E5", "C5"]:
        CodyNick.CJP_Sound_Maker.play_until_done(cody, note, 130)


def hear_wake_phrase(speech_in):
    listener = speech_in.listen(
        commands=WAKE_PHRASES, min_confidence=0.45, device="auto"
    )
    try:
        for event in listener:
            if event.get("accepted"):
                print("Heard: Wake up", flush=True)
                return
    finally:
        listener.stop()


def hear_question(speech_in):
    listener = speech_in.listen(
        commands=None, min_confidence=0.35, device="auto"
    )
    started = time.monotonic()
    try:
        while time.monotonic() - started < QUESTION_TIMEOUT:
            event = listener.get(timeout=0.25)
            if event and event.get("accepted"):
                question = event.get("text", "").strip()
                if question:
                    return question
        return None
    finally:
        listener.stop()


def speak_answer(speech_out, answer):
    result = speech_out.tts(
        ";;;" + answer, "llm_answer", speaker="speaker1"
    )
    if not result.get("ok"):
        raise RuntimeError(result.get("message", "TTS generation failed."))
    playback = speech_out.speak("llm_answer", device="auto", volume=100)
    if not playback.get("ok"):
        raise RuntimeError(playback.get("message", "Playback failed."))


def main():
    cody = CodyNick.CN()
    speech_out = CodyNickAI(workspace="/home/client")
    speech_in = CodyNickAI(workspace="/home/client")
    local_ai = CodyNickAI(workspace="/home/client")
    try:
        if not cody.ensure_connected():
            raise RuntimeError("CodyJoy Pro was not found.")

        print("Loading text-to-speech...", flush=True)
        status = speech_out.load_app("tts", model="fast", language="en")
        if not status.get("ok"):
            raise RuntimeError(status.get("message", "TTS failed to load."))
        print("Text-to-speech is ready.", flush=True)

        print("Loading speech recognition...", flush=True)
        speech_in.load_stt(model="small", language="en")
        print("Speech recognition is ready.", flush=True)

        print("Loading local AI...", flush=True)
        local_ai.load_llm()
        print("Local AI is ready. Say: Wake up", flush=True)

        running = True
        while running:
            waiting_effect(cody)
            hear_wake_phrase(speech_in)
            wake_effect(cody)
            speak_answer(speech_out, "I am listening.")

            while running:
                listening_effect(cody)
                question = hear_question(speech_in)
                if question is None:
                    print("No speech for 10 seconds. Returning to sleep.", flush=True)
                    break

                print("You:", question, flush=True)
                normalized = question.lower().strip()
                if normalized in SLEEP_PHRASES:
                    goodbye_effect(cody)
                    speak_answer(speech_out, "Going to sleep.")
                    break
                if normalized in STOP_PHRASES:
                    goodbye_effect(cody)
                    speak_answer(speech_out, "Goodbye.")
                    running = False
                    break

                processing_effect(cody)
                answer = local_ai.ask(
                    question,
                    system_prompt=(
                        "Answer using one complete sentence of 1 to 9 words. "
                        "Never use more than 9 words. Be friendly and accurate."
                    ),
                    max_tokens=20,
                    temperature=0.2,
                ).strip()
                if len(answer.split()) > 9:
                    answer = " ".join(answer.split()[:9])
                if not answer:
                    answer = "I could not answer that."

                print("AI:", answer, flush=True)
                answering_effect(cody)
                speak_answer(speech_out, answer)
    finally:
        speech_in.close()
        speech_out.close()
        local_ai.close()
        CodyNick.RGB_Matrix.clear(cody)
        cody.close()
        print("Conversation stopped.", flush=True)


if __name__ == "__main__":
    main()
