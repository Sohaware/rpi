"""CodyNick 0.5.3 demo: trigger camera OCR with the joystick and show a color."""
from difflib import SequenceMatcher
import time
from pathlib import Path

import CodyNick
from codynick_ai import CodyNickAI


JOYSTICK_DEVICE = "CJP"
MATCH_TEXT = "codynick"
OCR_CONFIDENCE = 0.20
MATCH_SIMILARITY = 0.80
RESULT_SECONDS = 5


def fill_matrix(cody, color):
    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, color)


def text_match_score(text, target):
    normalized = "".join(character for character in text.casefold()
                         if character.isalnum())
    target = "".join(character for character in target.casefold()
                     if character.isalnum())
    if not normalized or not target:
        return 0.0
    if target in normalized:
        return 1.0
    lengths = range(max(1, len(target) - 1), len(target) + 2)
    candidates = (normalized[start:start + length]
                  for length in lengths
                  for start in range(max(1, len(normalized) - length + 1)))
    return max((SequenceMatcher(None, target, candidate).ratio()
                for candidate in candidates), default=0.0)


def open_usb_camera():
    nodes = sorted(Path("/sys/class/video4linux").glob("video*"))
    candidates = [int(node.name[5:]) for node in nodes
                  if "/usb" in str((node / "device").resolve())]
    if not candidates:
        raise RuntimeError("No USB webcam found. Connect it and run again.")
    for index in candidates:
        ai = CodyNickAI(workspace="/home/client", camera_index=index)
        try:
            ai.open_camera()
            print(f"USB camera /dev/video{index} opened", flush=True)
            return ai
        except Exception as error:
            print(f"/dev/video{index}: {error}", flush=True)
            ai.close()
    raise RuntimeError("No USB camera returned an image. Check whether it is in use.")


def main():
    cody = CodyNick.CN()
    ai = None
    cody_ready = False
    try:
        if not cody.ensure_connected():
            raise RuntimeError("CodyNick gadget not found. Connect it and run again.")
        cody_ready = True
        ai = open_usb_camera()
        CodyNick.RGB_Matrix.clear(cody)
        print("Move the CodyJoy Pro joystick UP to take a picture and read its text.", flush=True)
        while "UP" not in CodyNick.Joystick.states(cody, JOYSTICK_DEVICE):
            time.sleep(0.1)

        name = "joystick_ocr"
        print("Joystick UP: taking picture...", flush=True)
        print("Picture:", ai.take_picture(
            name, cody=cody, get_ready_sound=True), flush=True)
        print("Loading English OCR...", flush=True)
        ai.load_app("ocr", model="standard", languages=["en"])
        result = ai.read_text(
            name,
            confidence=OCR_CONFIDENCE,
            preprocessing="scene",
            perspective="auto",
            save_visual=True,
        )
        text = result["text"]
        match_score = text_match_score(text, MATCH_TEXT)
        matched = match_score >= MATCH_SIMILARITY
        fill_matrix(cody, "#00FF00" if matched else "#FF0000")

        print("\nRecognized text:", flush=True)
        print(text or "[No readable text found]", flush=True)
        print("Result: CODYNICK FOUND - LEDs GREEN" if matched
              else "Result: CODYNICK NOT FOUND - LEDs RED", flush=True)
        print(f"Text match score: {match_score:.2f}", flush=True)
        print("Annotated picture:", result["annotated_image"], flush=True)
        print("JSON result:", result["json_result"], flush=True)
        time.sleep(RESULT_SECONDS)
        CodyNick.RGB_Matrix.clear(cody)
    finally:
        if ai is not None:
            ai.close()
        if cody_ready:
            try:
                CodyNick.RGB_Matrix.clear(cody)
            except Exception:
                pass
        cody.close()


if __name__ == "__main__":
    main()
