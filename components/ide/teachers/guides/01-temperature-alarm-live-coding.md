# CodyNick Fabric Presenter Guide: Build a CodyNick Temperature Alarm

## Session goal

Build one program in eight small steps. The audience first sees how easily Python can
control a physical LED, then gradually adds blinking, joystick input, a display, a
sensor, temperature colors, an alarm melody, and joystick alarm control.

These first examples intentionally use the simplest possible code. They do not include
connection checks, error handling, or cleanup structures. The goal is to make the first
experience with CodyNick clear and approachable.

Do not paste the final program at the beginning. Type each step live, run it, invite the
audience to predict the result, and then change the existing program for the next step.

## Equipment

- Raspberry Pi running CodyNick
- CodyJoy Pro
- Temperature sensor
- Stand-alone seven-segment display
- Python IDE at `http://10.42.0.1/code/`

## Presentation rhythm

For every step:

1. Ask the engaging question before showing the new code.
2. Let the audience suggest an answer.
3. Type the small change.
4. Ask the audience to predict the result.
5. Select **Run This File** and observe the hardware and live terminal.

---

## Step 1: Light One RGB LED

### Ask before starting

> How many lines of Python do you think we need to control a real LED?

Explain that `CodyNick.CN()` creates the connection and LED number `0` is the first LED
on the RGB matrix. A color is written as red, green, and blue values in hexadecimal.

```python
import time
import CodyNick

cody = CodyNick.CN()

CodyNick.RGB_Matrix.set(cody, 0, "#00FF00")
time.sleep(3)

CodyNick.RGB_Matrix.clear(cody)
```

### Point out

- `0` selects the first LED.
- `#00FF00` means green.
- `time.sleep(3)` keeps it visible for three seconds.
- `clear` turns the LED off at the end.

---

## Step 2: Make the LED Blink

### Ask before starting

> A computer follows instructions very quickly. How can we make it wait long enough for
> our eyes to see an LED blink?

Replace the single LED command and three-second wait with this loop:

```python
import time
import CodyNick

cody = CodyNick.CN()


for count in range(5):
    CodyNick.RGB_Matrix.set(cody, 0, "#00FF00")
    time.sleep(0.5)
    CodyNick.RGB_Matrix.set(cody, 0, "#000000")
    time.sleep(0.5)

```

### Point out

- `range(5)` repeats the indented instructions five times.
- `#000000` means no red, green, or blue, so the LED is off.
- The two half-second waits create an obvious rhythm.

Invite the audience to predict what changing `0.5` to `0.1` will do.

---

## Step 3: Control LEDs with the Joystick

### Ask before starting

> Can one physical control choose which light Python turns on?

Move the joystick up, right, down, and left. One LED in the corresponding part of the
matrix lights up in a different color. Press the joystick to light the center LED white.

```python
import time
import CodyNick

cody = CodyNick.CN()

while True:
    direction = CodyNick.Joystick.states(cody, "CJP")
    CodyNick.RGB_Matrix.clear(cody)

    if "CLICK" in direction:
        CodyNick.RGB_Matrix.set(cody, 6, "#FFFFFF")
    elif "UP" in direction:
        CodyNick.RGB_Matrix.set(cody, 13, "#0000FF")
    elif "RIGHT" in direction:
        CodyNick.RGB_Matrix.set(cody, 4, "#00FF00")
    elif "DOWN" in direction:
        CodyNick.RGB_Matrix.set(cody, 1, "#FF0000")
    elif "LEFT" in direction:
        CodyNick.RGB_Matrix.set(cody, 8, "#FFFF00")

    time.sleep(0.1)
```

### Point out

- `states` reads the current joystick direction.
- Up uses LED 13 in blue.
- Right uses LED 4 in green.
- Down uses LED 1 in red.
- Left uses LED 8 in yellow.
- Clicking uses LED 6 in white.
- `if` and `elif` choose only one LED at a time.
- The matrix is cleared before showing the current direction.
- `while True` keeps reading the joystick until the program is stopped.

---

## Step 4: Show a Fixed Number

### Ask before starting

> If Python can control one light, can it also send a complete number to a display with
> one instruction?

Replace the blinking code with a seven-segment display command:

```python
import CodyNick

cody = CodyNick.CN()

CodyNick.Seven_Segment.display(cody, "Stand-Alone", 25)
```

### Point out

- `"Stand-Alone"` selects the separate seven-segment display.
- `25` is the value sent to the display.

---

## Step 5: Show a Counter

### Ask before starting

> The display is showing data from our program. What should change if we want the display
> to show progress instead of one fixed value?

Change the fixed display command to a loop:

```python
import time
import CodyNick

cody = CodyNick.CN()


for number in range(1, 11):
    CodyNick.Seven_Segment.display(cody, "Stand-Alone", number)
    print("Count:", number)
    time.sleep(1)

```

### Point out

- `range(1, 11)` produces the numbers `1` through `10`.
- The same variable is shown on the physical display and in the live terminal.
- Software variables can directly represent real-world output.

---

## Step 6: Display the Measured Temperature

### Ask before starting

> So far, Python has displayed numbers that we chose. How can the physical world choose
> the number instead?

Replace the counter with a continuous sensor loop:

```python
import time
import CodyNick

cody = CodyNick.CN()


while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    temperature = round(temperature, 1)

    CodyNick.Seven_Segment.display(cody, "Stand-Alone", temperature)
    print("Temperature:", temperature, "C")

    time.sleep(1)

```

### Point out

- `read(cody)` gets a current measurement from the sensor.
- `round(..., 1)` keeps one digit after the decimal point.
- `while True` continues until the presenter stops the script.
- The one-second pause gives a readable update rate.

Ask someone to gently warm the sensor and watch the number respond.

---

## Step 7: Add Temperature Colors

### Ask before starting

> Can someone understand whether a temperature is cold, comfortable, or hot more quickly
> from a number or from a color?

Add the temperature decision and use a loop to color all 16 LEDs:

```python
import time
import CodyNick

cody = CodyNick.CN()


while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    temperature = round(temperature, 1)

    CodyNick.Seven_Segment.display(cody, "Stand-Alone", temperature)

    if temperature < 20:
        color = "#0000FF"
    elif temperature <= 30:
        color = "#00FF00"
    else:
        color = "#FF0000"

    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, color)

    print("Temperature:", temperature, "C")
    time.sleep(1)

```

### Point out

- Below 20 C is blue.
- From 20 C through 30 C is green.
- Above 30 C is red.
- `if`, `elif`, and `else` turn one measurement into one of three decisions.
- `range(16)` applies the chosen color to the complete matrix.

---

## Step 8: Add the Alarm and Joystick Inhibit

### Ask before starting

> A real alarm may need to be silenced while someone investigates. How can one joystick
> button act as both the silence control and the re-enable control?

Start with two variables that remember the alarm state:

```python
alarm_enabled = True
was_clicked = False
```

Then build the final program:

```python
import time
import CodyNick

cody = CodyNick.CN()

alarm_enabled = True
was_clicked = False


while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    temperature = round(temperature, 1)

    CodyNick.Seven_Segment.display(cody, "Stand-Alone", temperature)

    if temperature < 20:
        color = "#0000FF"
    elif temperature <= 30:
        color = "#00FF00"
    else:
        color = "#FF0000"

    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, color)

    is_clicked = CodyNick.Joystick.click(cody, "CJP")

    if is_clicked and not was_clicked:
        alarm_enabled = not alarm_enabled

        if alarm_enabled:
            print("Alarm enabled")
        else:
            print("Alarm inhibited")

    was_clicked = is_clicked

    if temperature > 30 and alarm_enabled:
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "C6", 120)
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "E6", 120)
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "G6", 120)
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "E6", 120)

    print("Temperature:", temperature, "C")

    time.sleep(0.3)

```

### Point out

- `alarm_enabled` remembers whether sound is permitted.
- `was_clicked` allows one physical press to cause only one toggle.
- `not alarm_enabled` changes enabled to inhibited and inhibited to enabled.
- The red visual warning remains active while the audible alarm is inhibited.
- The alarm melody is `C6`, `E6`, `G6`, `E6`.
- The joystick is checked between complete melody cycles.

---

## Step 9: Connect to AI and Take a Picture

### Ask before starting

> We have given our program sensor inputs. What new things could it understand if we
> gave it eyes?

The camera has not been connected during the earlier steps. Connect the USB camera now
and wait a few seconds for the Raspberry Pi to recognize it.

Replace the previous program with this short camera program:

```python
import CodyNick
from codynick_ai import CodyNickAI

cody = CodyNick.CN()
ai = CodyNickAI(workspace="/home/client", camera_index=0)

picture = ai.take_picture(
    "camera_demo",
    cody=cody,
    get_ready_sound=True
)

print("Picture saved:", picture)

ai.close()
cody.close()
```

Run the program, then open **Images** in the IDE and select `camera_demo.jpg` to show
the captured picture to the audience. Running the program again replaces the same
picture instead of filling the Images folder with many files.

### Point out

- `CodyNickAI` connects the student program to the installed AI tools.
- `cody=cody` connects the camera activity to CodyJoy Pro.
- `get_ready_sound=True` plays the get-ready and shutter sounds.
- `take_picture()` captures one image and releases the camera after the shot.
- `"camera_demo"` is the reusable image name.
- The image is stored in `/home/client/images` and appears under **Images** in the IDE.
- Taking a picture is the first step. The same picture can next be used for object
  detection, OCR, face tools, or another AI model.

---

## Step 10: Detect Objects in the Picture

### Ask before starting

> The camera can take a picture, but can the computer tell us what is inside it?

Place a few familiar objects in front of the camera, such as a bottle, cup, chair, or
person. Extend the camera program so it captures a fresh picture and analyzes it:

```python
import CodyNick
from codynick_ai import CodyNickAI

cody = CodyNick.CN()
ai = CodyNickAI(workspace="/home/client", camera_index=0)

picture = ai.take_picture(
    "camera_demo",
    cody=cody,
    get_ready_sound=True
)

print("Picture saved:", picture)

ai.load_app("yolo", model="nano")
result = ai.detect_objects("camera_demo")

print("Objects found:", len(result["detections"]))

for item in result["detections"]:
    print(item["class_name"], item["confidence"])

ai.close()
cody.close()
```

After the result appears, open **Images**, open the `results` folder, and select
`camera_demo_objects.jpg`. Show how the AI has drawn a box and label around each
recognized object.

### Point out

- `load_app("yolo", model="nano")` loads the fast object-detection model.
- `detect_objects("camera_demo")` analyzes the picture captured by the program.
- `result["detections"]` contains the objects found by the model.
- Each result includes a class name and a confidence score.
- The annotated image is saved under **Images → results**.
- The model may miss an object or label it incorrectly. Better lighting and a clear
  view usually improve the result.

---

## Step 11: Control the LEDs with Your Voice

### Ask before starting

> We have controlled the lights with code and a joystick. Can we control them without
> touching the computer or the gadget at all?

Use a USB microphone, or use the microphone built into the USB camera if it has one.
Keep it close enough to hear the presenter clearly.

In the IDE, open **CodyNick Examples → `voice_led_colors.py`** and select
**Run This File**. Wait until the terminal says that offline English speech recognition
is ready, then say one command at a time:

- `red`
- `green`
- `blue`
- `yellow`
- `white`
- `purple`
- `lights off`
- `stop listening`

The installed example includes useful progress messages. This shorter presenter version
keeps the same commands, recognition settings, hardware behavior, and cleanup logic:

```python
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
            raise RuntimeError("CodyNick gadget not found.")

        ai.load_app("stt", model="small", language="en")

        listener = ai.listen(
            commands=COMMANDS,
            min_confidence=0.45,
            device="auto"
        )

        for event in listener:
            if not event.get("accepted"):
                continue

            command = event["matched_command"]
            print("Heard:", command)

            if command == "stop listening":
                break
            elif command == "lights off":
                CodyNick.RGB_Matrix.clear(cody)
            else:
                fill_matrix(cody, COMMAND_COLORS[command])

    finally:
        if listener is not None:
            listener.stop()

        ai.close()
        CodyNick.RGB_Matrix.clear(cody)
        cody.close()


main()
```

### Point out

- `load_app("stt", ...)` loads offline speech-to-text. The spoken audio does not need
  to be sent to an internet service.
- `COMMANDS` limits recognition to the phrases used by this demonstration.
- `device="auto"` selects an available USB or camera microphone.
- `min_confidence=0.45` rejects uncertain matches below the selected confidence level.
- `lights off` clears the LEDs but keeps the microphone listening.
- `stop listening` ends the program and turns the LEDs off.
- The `finally` section releases the microphone and clears the hardware even when the
  program is stopped unexpectedly.

### Demonstration tips

- Wait for the ready message before speaking.
- Speak one command clearly, then pause briefly for the result.
- Reduce nearby conversation and music while demonstrating recognition.
- If a command is rejected, move closer to the microphone and repeat it normally.

## Closing audience questions

- Which thresholds would you use for a refrigerator, greenhouse, or classroom?
- What other sensor could replace the temperature sensor?
- What could the joystick control besides the alarm?
- How could the dashboard or cloud record the temperature history?
- What could an AI model discover in the picture we just captured?
- How could the program react when it recognizes a particular object?
- What other spoken commands could control a CodyNick project?

## Presenter reminder

Keep the code visible while demonstrating the hardware response. The purpose is not to
memorize every command; it is to show the repeated pattern:

1. Read an input.
2. Make a decision.
3. Control an output.
4. Repeat safely.
