"""CodyNick 0.4.0 demo: control the RGB matrix with offline voice commands."""
import CodyNick
from codynick_ai import CodyNickAI


COMMAND_COLORS = {
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "white": "#FFFFFF",
    "purple": "#FF00FF",
}
COMMANDS = list(COMMAND_COLORS) + ["lights off", "stop listening"]


def fill_matrix(cody, color):
    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, color)


def main():
    cody = CodyNick.CN()
    ai = CodyNickAI(workspace="/home/client")
    listener = None
    try:
        if not cody.ensure_connected():
            raise RuntimeError("CodyNick gadget not found. Connect it and run again.")
        print("Loading offline English speech recognition...", flush=True)
        ai.load_app("stt", model="small", language="en")
        print("Say: red, green, blue, yellow, white, purple, lights off, or stop listening.", flush=True)
        listener = ai.listen(commands=COMMANDS, min_confidence=0.45, device="auto")
        for event in listener:
            if not event.get("accepted"):
                continue
            command = event["matched_command"]
            score = event.get("confidence", 0.0)
            print(f"Heard: {command} (score {score:.2f})", flush=True)
            if command == "stop listening":
                break
            if command == "lights off":
                CodyNick.RGB_Matrix.clear(cody)
            else:
                fill_matrix(cody, COMMAND_COLORS[command])
    finally:
        if listener is not None:
            listener.stop()
        ai.close()
        CodyNick.RGB_Matrix.clear(cody)
        cody.close()
        print("Voice demo stopped; LEDs are off.", flush=True)


if __name__ == "__main__":
    main()
