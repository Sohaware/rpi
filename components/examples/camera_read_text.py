"""CodyNick 0.5.3 demo: photograph English text and read it offline."""
from pathlib import Path
import CodyNick
from codynick_ai import CodyNickAI


OCR_CONFIDENCE = 0.20


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
        name = "camera_text"
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
        items = result["items"]
        print("\nRecognized text:", flush=True)
        print(result["text"] or "[No readable text found]", flush=True)
        if items:
            average = sum(item["confidence"] for item in items) / len(items)
            print(f"\nText regions: {len(items)}; average confidence: {average:.2f}", flush=True)
        else:
            print("Try larger printed English text, steadier framing, and brighter light.", flush=True)
        print("Annotated picture:", result["annotated_image"], flush=True)
        print("JSON result:", result["json_result"], flush=True)
        print("See Images/results in the IDE.", flush=True)
    finally:
        if ai is not None:
            ai.close()
        cody.close()


if __name__ == "__main__":
    main()
