# LED Matrix

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Purpose Of This Page</h2>

This page explains how to control the CodyNick 8 by 8 monochrome LED Matrix using Python.

The LED Matrix can be used in two main ways:

- Display scrolling text.
- Turn individual pixels on and off.

By the end of this page, students will be able to:

- Display text on the LED Matrix.
- Choose the text scrolling speed.
- Turn one pixel on.
- Turn one pixel off.
- Clear the whole matrix.

<img src="https://dl.sohaware.com/uploads/projects/codynick/img/led_matrix.JPG" alt="CodyNick LED Matrix" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 1 - CodyNick 8 by 8 monochrome LED Matrix.
</div>

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Start Code</h2>

Every CodyNick Python script should import the CodyNick library and connect to the CodyNick device.

```python
import CodyNick

cn = CodyNick.CN()
```

The variable `cn` represents the connected CodyNick device.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Display Scrolling Text</h2>

Use `LED_Matrix.display_text()` to show scrolling text.

Function format:

```python
CodyNick.LED_Matrix.display_text(cn, text, speed)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `text` | Text to display |
| `speed` | Text speed: `0`, `1`, `2`, `"slow"`, `"medium"`, or `"fast"` |

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.LED_Matrix.display_text(cn, "Hello", "slow")
```

This shows the word `Hello` with slow scrolling speed.

Another example:

```python
CodyNick.LED_Matrix.display_text(cn, "CodyPy", 2)
```

This shows `CodyPy` with fast scrolling speed.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Text Speed</h2>

Text speed can be written as a number or as a word.

| Number | Word | Meaning |
|---:|---|---|
| `0` | `"slow"` | Slow scrolling |
| `1` | `"medium"` | Medium scrolling |
| `2` | `"fast"` | Fast scrolling |

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Pixel Coordinates</h2>

The LED Matrix has 8 columns and 8 rows.

Both `x` and `y` use values from `0` to `7`.

The exact physical orientation depends on the gadget mounting, so it is best to test a few points when first using a new matrix.

Example coordinates:

```text
(0,7)                         (7,7)






(0,0)                         (7,0)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Turn One Pixel On Or Off</h2>

Use `LED_Matrix.set_pixel()` to choose the state directly.

Function format:

```python
CodyNick.LED_Matrix.set_pixel(cn, x, y, state)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `x` | Horizontal coordinate from `0` to `7` |
| `y` | Vertical coordinate from `0` to `7` |
| `state` | `1` or `True` for on, `0` or `False` for off |

Examples:

```python
CodyNick.LED_Matrix.set_pixel(cn, 3, 4, 1)
CodyNick.LED_Matrix.set_pixel(cn, 3, 4, 0)
```

The first line turns pixel `(3,4)` on.

The second line turns the same pixel off.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Turn A Pixel On</h2>

Use `LED_Matrix.on()` when the intent is clearly to turn on a pixel.

```python
CodyNick.LED_Matrix.on(cn, 3, 4)
```

This turns pixel `(3,4)` on.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Turn A Pixel Off</h2>

Use `LED_Matrix.off()` when the intent is clearly to turn off a pixel.

```python
CodyNick.LED_Matrix.off(cn, 3, 4)
```

This turns pixel `(3,4)` off.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Clear The Matrix</h2>

Use `LED_Matrix.clear()` to turn off all pixels on the matrix.

```python
CodyNick.LED_Matrix.clear(cn)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Example: Blink One Pixel</h2>

```python
import CodyNick
import time

cn = CodyNick.CN()

CodyNick.LED_Matrix.on(cn, 3, 4)
time.sleep(1)
CodyNick.LED_Matrix.off(cn, 3, 4)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Example: Move One Pixel</h2>

```python
import CodyNick
import time

cn = CodyNick.CN()

x = 0
y = 4

while True:
    CodyNick.LED_Matrix.clear(cn)
    CodyNick.LED_Matrix.on(cn, x, y)
    x = (x + 1) % 8
    time.sleep(0.2)
```

This moves one pixel across the matrix and brings it back from the opposite side.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Example: Show Joystick Direction</h2>

```python
import CodyNick
import time

cn = CodyNick.CN()

while True:
    states = CodyNick.Joystick.states(cn)

    if "UP" in states:
        CodyNick.LED_Matrix.display_text(cn, "UP", "slow")
    elif "DOWN" in states:
        CodyNick.LED_Matrix.display_text(cn, "DOWN", "slow")
    elif "LEFT" in states:
        CodyNick.LED_Matrix.display_text(cn, "LEFT", "slow")
    elif "RIGHT" in states:
        CodyNick.LED_Matrix.display_text(cn, "RIGHT", "slow")

    time.sleep(0.1)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Function Summary</h2>

| Function | Purpose | Example |
|---|---|---|
| `LED_Matrix.display_text(cn, text, speed)` | Show scrolling text | `display_text(cn, "Hello", "slow")` |
| `LED_Matrix.set_pixel(cn, x, y, state)` | Set one pixel on or off | `set_pixel(cn, 3, 4, 1)` |
| `LED_Matrix.on(cn, x, y)` | Turn one pixel on | `on(cn, 3, 4)` |
| `LED_Matrix.off(cn, x, y)` | Turn one pixel off | `off(cn, 3, 4)` |
| `LED_Matrix.clear(cn)` | Turn off all pixels | `clear(cn)` |

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Practice Tasks</h2>

Try these exercises:

1. Display your name on the LED Matrix.
2. Show the same text with slow, medium, and fast speed.
3. Turn pixel `(0,0)` on.
4. Turn pixel `(7,7)` on.
5. Blink pixel `(3,4)` five times.
6. Draw a horizontal line using a loop.
7. Move one pixel around the border of the matrix.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Common Mistakes</h2>

Coordinates must stay between `0` and `7`:

```python
CodyNick.LED_Matrix.on(cn, 7, 7)
```

This is outside the matrix:

```python
CodyNick.LED_Matrix.on(cn, 8, 0)
```

Text speed must be one of the supported values:

```python
CodyNick.LED_Matrix.display_text(cn, "Hello", "fast")
```

The LED Matrix uses ASCII text only for scrolling text.

If old pixels stay on, clear the matrix before drawing the next frame:

```python
CodyNick.LED_Matrix.clear(cn)
```

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Page summary:</strong><br>
The LED Matrix can show scrolling text or individual pixels. Use `display_text()` for messages, and use `set_pixel()`, `on()`, `off()`, and `clear()` to draw with pixels.
</div>
