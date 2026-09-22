# RGB LED Matrix

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Purpose Of This Page</h2>

This page explains how to control the 4 by 4 RGB LED Matrix on the CodyJoy Pro using Python.

By the end of this page, students will be able to:

- Turn on one RGB LED by LED number.
- Turn on one RGB LED by `(x, y)` coordinate.
- Use built-in color codes.
- Use RGB hex colors.
- Use RGB percentage colors.
- Clear all RGB LEDs.

<img src="/docs/assets/gadgets/cjp_neo.png" alt="CodyJoy Pro RGB LED Matrix" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 1 - CodyJoy Pro with the 4 by 4 RGB LED Matrix.
</div>

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Start Code</h2>

Every CodyNick Python script should import the CodyNick library and connect to the CodyNick device.

```python
import CodyNick

cn = CodyNick.CN()
```

The variable `cn` represents the connected CodyNick device. It is passed to the CodyNick functions so Python knows which device to control.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">RGB LED Number Layout</h2>

The CodyJoy Pro RGB LEDs are numbered as shown below:

```text
15  14  13  12
 8   9  10  11
 7   6   5   4
 0   1   2   3
```

Important positions:

- LED `0` is the bottom-left LED.
- LED `3` is the bottom-right LED.
- LED `15` is the top-left LED.
- LED `12` is the top-right LED.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Turn On One LED By Number</h2>

Use `RGB_Matrix.set()` to turn on one LED.

Function format:

```python
CodyNick.RGB_Matrix.set(cn, led_number, color)
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.RGB_Matrix.set(cn, 15, "#FF0000")
```

This turns LED `15` red.

Another example:

```python
CodyNick.RGB_Matrix.set(cn, 0, "#00FF00")
```

This turns LED `0` green.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Clear The RGB Matrix</h2>

Use `RGB_Matrix.clear()` to turn off all RGB LEDs.

```python
CodyNick.RGB_Matrix.clear(cn)
```

Example:

```python
import CodyNick
import time

cn = CodyNick.CN()

CodyNick.RGB_Matrix.set(cn, 15, "#FF0000")
time.sleep(1)
CodyNick.RGB_Matrix.clear(cn)
```

This turns LED `15` red for one second, then turns all LEDs off.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Built-In Color Codes</h2>

The easiest way to choose a color is to use one of the built-in color codes from `0` to `7`.

| Code | Name | Hex |
|---:|---|---|
| 0 | Red | `#FF0000` |
| 1 | Cyan | `#00FFFF` |
| 2 | Blue | `#0000FF` |
| 3 | Yellow | `#FFFF00` |
| 4 | Magenta | `#FF00FF` |
| 5 | Green | `#00FF00` |
| 6 | Orange | `#FF8000` |
| 7 | White | `#FFFFFF` |

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.RGB_Matrix.set(cn, 15, 0)
```

This turns LED `15` red, because color code `0` means red.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">RGB Hex Colors</h2>

Students can also use RGB hex colors.

An RGB hex color starts with `#` and has six hexadecimal characters:

```python
"#RRGGBB"
```

`RR` controls red, `GG` controls green, and `BB` controls blue.

Common examples:

| Color | Hex |
|---|---|
| Red | `#FF0000` |
| Green | `#00FF00` |
| Blue | `#0000FF` |
| Cyan | `#00FFFF` |
| Yellow | `#FFFF00` |
| Magenta | `#FF00FF` |
| White | `#FFFFFF` |

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.RGB_Matrix.set(cn, 12, "#00FFFF")
```

This turns LED `12` cyan.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">RGB Percentage Colors</h2>

Students can also describe a color with red, green, and blue percentages.

Format:

```python
[red_percent, green_percent, blue_percent]
```

Each number must be between `0` and `100`.

Examples:

| Color Input | Meaning |
|---|---|
| `[100, 0, 0]` | 100% red |
| `[0, 100, 0]` | 100% green |
| `[0, 0, 100]` | 100% blue |
| `[0, 100, 100]` | cyan |
| `[100, 100, 0]` | yellow |
| `[50, 0, 0]` | dim red |

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.RGB_Matrix.set(cn, 10, [0, 100, 100])
```

This turns LED `10` cyan.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Coordinate Layout</h2>

Students can also control LEDs by `(x, y)` coordinate.

The bottom-left LED is `(0, 0)`.

The top-right LED is `(3, 3)`.

```text
(0,3)  (1,3)  (2,3)  (3,3)
(0,2)  (1,2)  (2,2)  (3,2)
(0,1)  (1,1)  (2,1)  (3,1)
(0,0)  (1,0)  (2,0)  (3,0)
```

Use `RGB_Matrix.set_xy()` to control one LED by coordinate.

Function format:

```python
CodyNick.RGB_Matrix.set_xy(cn, x, y, color)
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.RGB_Matrix.set_xy(cn, 0, 0, "#FF0000")
```

This turns the bottom-left LED red.

Another example:

```python
CodyNick.RGB_Matrix.set_xy(cn, 3, 3, 2)
```

This turns the top-right LED blue, because color code `2` means blue.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Example: Four Corners</h2>

This example lights the four corner LEDs with different colors.

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.RGB_Matrix.clear(cn)

CodyNick.RGB_Matrix.set_xy(cn, 0, 0, 0)          # bottom-left red
CodyNick.RGB_Matrix.set_xy(cn, 3, 0, 5)          # bottom-right green
CodyNick.RGB_Matrix.set_xy(cn, 0, 3, 2)          # top-left blue
CodyNick.RGB_Matrix.set_xy(cn, 3, 3, "#FFFF00")  # top-right yellow
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Example: Show All Built-In Colors</h2>

This example shows all eight built-in colors one by one.

```python
import CodyNick
import time

cn = CodyNick.CN()

for color_code in range(8):
    CodyNick.RGB_Matrix.clear(cn)
    CodyNick.RGB_Matrix.set(cn, color_code, color_code)
    time.sleep(0.5)
```

In this loop, the LED number and the color code are both using `color_code`.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Example: Center LEDs</h2>

The center four LEDs are:

```text
(1,2)  (2,2)
(1,1)  (2,1)
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.RGB_Matrix.clear(cn)

CodyNick.RGB_Matrix.set_xy(cn, 1, 1, "#FF0000")
CodyNick.RGB_Matrix.set_xy(cn, 2, 1, "#00FF00")
CodyNick.RGB_Matrix.set_xy(cn, 1, 2, "#0000FF")
CodyNick.RGB_Matrix.set_xy(cn, 2, 2, "#FFFFFF")
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Practice Tasks</h2>

Try these exercises:

1. Turn on LED `0` in red.
2. Turn on LED `12` in blue.
3. Clear the matrix after two seconds.
4. Turn on all four corners with different colors.
5. Use `set_xy()` to light the center four LEDs.
6. Create a loop that moves one light from LED `0` to LED `15`.
7. Use percentage colors to make dim red, dim green, and dim blue.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Common Mistakes</h2>

Hex colors must be written as strings:

```python
CodyNick.RGB_Matrix.set(cn, 0, "#FF0000")
```

This is not correct:

```python
CodyNick.RGB_Matrix.set(cn, 0, #FF0000)
```

Color percentages must use numbers from `0` to `100`:

```python
CodyNick.RGB_Matrix.set(cn, 0, [100, 50, 0])
```

Coordinates must be between `0` and `3`:

```python
CodyNick.RGB_Matrix.set_xy(cn, 3, 3, 7)
```

This is outside the matrix:

```python
CodyNick.RGB_Matrix.set_xy(cn, 4, 0, 7)
```

If old LEDs stay on, clear the matrix before drawing the next pattern:

```python
CodyNick.RGB_Matrix.clear(cn)
```

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Page summary:</strong><br>
The RGB LED Matrix can be controlled by LED number or by `(x, y)` coordinate. Colors can be written as built-in color codes, RGB hex values, or RGB percentage lists.
</div>
