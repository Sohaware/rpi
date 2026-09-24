# CodyJoy Pro Test

## What this checks

This test checks the CodyJoy Pro joystick, buzzer, and the connected RGB matrix. Move
the joystick in each direction. Each movement replaces the previous pattern. Click the
joystick to light the four center LEDs. The pattern remains until the next action.

```python
import time
import CodyNick

cody = CodyNick.CN()
last_action = ""

while True:
    joystick = CodyNick.Joystick.states(cody, "CJP")
    action = ""

    if "CLICK" in joystick:
        action = "CLICK"
    elif "UP" in joystick:
        action = "UP"
    elif "RIGHT" in joystick:
        action = "RIGHT"
    elif "DOWN" in joystick:
        action = "DOWN"
    elif "LEFT" in joystick:
        action = "LEFT"

    if action and action != last_action:
        CodyNick.RGB_Matrix.clear(cody)

        if action == "UP":
            leds, color, note = [15, 14, 13, 12], "#0000FF", "C7"
        elif action == "RIGHT":
            leds, color, note = [12, 11, 4, 3], "#00FF00", "E7"
        elif action == "DOWN":
            leds, color, note = [0, 1, 2, 3], "#FF0000", "G7"
        elif action == "LEFT":
            leds, color, note = [15, 8, 7, 0], "#FFFF00", "B7"
        else:
            leds, color, note = [9, 10, 6, 5], "#FFFFFF", "C8"

        for led in leds:
            CodyNick.RGB_Matrix.set(cody, led, color)

        CodyNick.CJP_Sound_Maker.play_until_done(cody, note, 150)
        print(action)
        last_action = action

    time.sleep(0.1)
```

## Expected result

- Up: top side blue with C7.
- Right: right side green with E7.
- Down: bottom side red with G7.
- Left: left side yellow with B7.
- Click: center four LEDs white with C8.

If one direction is missing but the others work, inspect or replace the joystick before
changing the program.
