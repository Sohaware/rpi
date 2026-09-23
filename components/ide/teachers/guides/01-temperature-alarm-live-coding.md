# Build a CodyNick Temperature Alarm

## Session goal

Build one program in seven small steps. Before typing each step, ask its audience question, invite two or three predictions, then run the code and observe the hardware together.

Equipment: Raspberry Pi with CodyNick installed, CodyJoy Pro, temperature sensor, and UltraSeg seven-segment display.

> Presenter rule: type the new lines live. Keep the pace calm and let the audience explain what changed before you explain it.

## 1. Light one LED

**Ask:** If one line of Python could control a real light, what color should we try first?

```python
import time
import CodyNick

cn = CodyNick.CN()
CodyNick.RGB_Matrix.set(cn, 0, "#00FF00")
time.sleep(3)
CodyNick.RGB_Matrix.clear(cn)
```

Point out that LED number `0` is the first LED and `(0, 255, 0)` means green.

## 2. Make it blink

**Ask:** What two actions must repeat to make a steady light blink?

```python
import time
import CodyNick

cn = CodyNick.CN()

for count in range(5):
    CodyNick.RGB_Matrix.set(cn, 0, "#00FF00")
    time.sleep(0.5)
    CodyNick.RGB_Matrix.clear(cn)
    time.sleep(0.5)
```

The loop repeats five times. The two pauses make the on and off states visible.

## 3. Show a fixed number

**Ask:** Where might a device need to show a number without using a computer screen?

```python
import time
import CodyNick

cn = CodyNick.CN()
CodyNick.Seven_Segment.display(cn, "UltraSeg", 25)
time.sleep(5)
```

The same program structure now controls a different gadget.

## 4. Show a counter

**Ask:** How could we turn the fixed display into a countdown, score, or visitor counter?

```python
import time
import CodyNick

cn = CodyNick.CN()

for number in range(10):
    CodyNick.Seven_Segment.display(cn, "UltraSeg", number)
    time.sleep(1)
```

`range(10)` supplies the numbers from 0 through 9.

## 5. Show the temperature

**Ask:** What changes when the displayed number comes from a sensor instead of our program?

```python
import time
import CodyNick

cn = CodyNick.CN()

while True:
    temperature = CodyNick.Temperature_Sensor.read(cn)
    if temperature is not None:
        CodyNick.Seven_Segment.display(cn, "UltraSeg", round(temperature))
        print("Temperature:", temperature, "C")
    time.sleep(1)
```

The loop keeps reading. `round()` makes the measurement suitable for the display.

## 6. Add temperature colors

**Ask:** Could someone understand the temperature from across the room without reading the number?

```python
import time
import CodyNick

cn = CodyNick.CN()

while True:
    temperature = CodyNick.Temperature_Sensor.read(cn)

    if temperature is None:
        time.sleep(1)
        continue

    CodyNick.Seven_Segment.display(cn, "UltraSeg", round(temperature))

    if temperature < 18:
        color = "#0000FF"
    elif temperature <= 30:
        color = "#00FF00"
    else:
        color = "#FF0000"

    for led in range(16):
        CodyNick.RGB_Matrix.set(cn, led, color)

    time.sleep(1)
```

Blue means below 18 C, green means 18 through 30 C, and red means above 30 C.

## 7. Add the alarm and joystick inhibit

**Ask:** If an alarm warns us successfully, how can we silence its sound without hiding the red warning light?

```python
import time
import CodyNick

cn = CodyNick.CN()

alarm_enabled = True
was_clicked = False

while True:
    temperature = CodyNick.Temperature_Sensor.read(cn)

    clicked = CodyNick.Joystick.click(cn, "CJP")
    if clicked and not was_clicked:
        alarm_enabled = not alarm_enabled
        print("Alarm enabled:", alarm_enabled)
    was_clicked = clicked

    if temperature is None:
        time.sleep(0.2)
        continue

    CodyNick.Seven_Segment.display(cn, "UltraSeg", round(temperature))

    if temperature < 18:
        color = "#0000FF"
    elif temperature <= 30:
        color = "#00FF00"
    else:
        color = "#FF0000"
        if alarm_enabled:
            CodyNick.CJP_Sound_Maker.play_until_done(cn, "C6", 120)
            CodyNick.CJP_Sound_Maker.play_until_done(cn, "E6", 120)
            CodyNick.CJP_Sound_Maker.play_until_done(cn, "G6", 180)
            CodyNick.CJP_Sound_Maker.play_until_done(cn, "E6", 120)

    for led in range(16):
        CodyNick.RGB_Matrix.set(cn, led, color)

    time.sleep(0.2)
```

The click changes `alarm_enabled` only once per press. The visual warning remains active when the sound is inhibited, and pressing the joystick again re-enables the melody.

## Closing discussion

Ask the audience:

- Which step changed this from a demonstration into a useful device?
- What other sensor could replace temperature?
- What should a real product do if its sensor is disconnected?

End by showing that the final project grew from one understandable line at a time.
