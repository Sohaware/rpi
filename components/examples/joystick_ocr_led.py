"""CodyNick 0.5.1 demo: trigger camera OCR with the joystick and show a color."""
import time
from pathlib import Path
from uuid import uuid4

import CodyNick
from codynick_ai import CodyNickAI


JOYSTICK_DEVICE = "CJP"
MATCH_TEXT = "codynick"


def fill_matrix(cody, color):
    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, color)


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
    try:
        if not cody.ensure_connected():
            raise RuntimeError("CodyNick gadget not found. Connect it and run again.")
        ai = open_usb_camera()
        CodyNick.RGB_Matrix.clear(cody)
        print("Move the CodyJoy Pro joystick UP to take a picture and read its text.", flush=True)
        while "UP" not in CodyNick.Joystick.states(cody, JOYSTICK_DEVICE):
            time.sleep(0.1)

        name = "joystick_ocr_" + uuid4().hex[:12]
        print("Joystick UP: taking picture...", flush=True)
        print("Picture:", ai.take_picture(name), flush=True)
        print("Loading English OCR...", flush=True)
        ai.load_app("ocr", model="standard", languages=["en"])
        result = ai.read_text(
            name,
            confidence=0.30,
            preprocessing="scene",
            perspective="auto",
            save_visual=True,
        )
        text = result["text"]
        normalized = "".join(character for character in text.casefold()
                             if character.isalnum())
        matched = MATCH_TEXT in normalized
        fill_matrix(cody, "#00FF00" if matched else "#FF0000")

        print("\nRecognized text:", flush=True)
        print(text or "[No readable text found]", flush=True)
        print("Result: CODYNICK FOUND - LEDs GREEN" if matched
              else "Result: CODYNICK NOT FOUND - LEDs RED", flush=True)
        print("Annotated picture:", result["annotated_image"], flush=True)
        print("JSON result:", result["json_result"], flush=True)
    finally:
        if ai is not None:
            ai.close()
        cody.close()


if __name__ == "__main__":
    main()
