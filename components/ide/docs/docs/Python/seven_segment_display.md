# Seven Segment Display

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Purpose Of This Page</h2>

This page explains how to show numbers on seven-segment display gadgets using Python.

The Seven Segment Display is useful for showing:

- Scores.
- Counts.
- Sensor values.
- Timer values.
- Simple numeric feedback.

By the end of this page, students will be able to:

- Display a positive number.
- Display a negative number.
- Display a decimal number.
- Update the displayed value inside a Python program.

<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 1 - CodyNick Seven Segment Display for showing numeric values.
</div>

<img src="/docs/assets/gadgets/ultraseg.png" alt="UltraSeg gadget" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 2 - UltraSeg gadget. It combines a seven-segment display with an ultrasonic sensor.
</div>

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Start Code</h2>

Every CodyNick Python script should import the CodyNick library and connect to the CodyNick device.

```python
import CodyNick

cn = CodyNick.CN()
```

The variable `cn` represents the connected CodyNick device.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Choose The Display Device</h2>

Every seven-segment command needs a device name.

| Device name | Meaning |
|---|---|
| `"Stand-Alone"` | Separate seven-segment display gadget |
| `"UltraSeg"` | Seven-segment display inside UltraSeg |

Names are flexible. For example, `"stand-alone"`, `"standalone"`, `"stand alone"`, `"ultraseg"`, and `"ultra-seg"` also work.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Display A Number</h2>

Use `Seven_Segment.display()` to show a number.

Function format:

```python
CodyNick.Seven_Segment.display(cn, device, value)
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.Seven_Segment.display(cn, "Stand-Alone", 1234)
```

This displays `1234`.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Display A Negative Number</h2>

The display can show negative values.

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.Seven_Segment.display(cn, "Stand-Alone", -123)
```

This displays `-123`.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Display A Decimal Number</h2>

The display can also show decimal values.

Example:

```python
import CodyNick

cn = CodyNick.CN()

CodyNick.Seven_Segment.display(cn, "UltraSeg", 1.234)
```

This displays `1.234` if the value fits on the display.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Using Strings Or Numbers</h2>

The value can be passed as a number:

```python
CodyNick.Seven_Segment.display(cn, "Stand-Alone", 1234)
```

It can also be passed as a string:

```python
CodyNick.Seven_Segment.display(cn, "Stand-Alone", "1234")
```

Both examples display the same value.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Display Range</h2>

The display is designed for short numeric values.

Typical useful values are:

| Type | Example |
|---|---|
| Positive integer | `1234` |
| Negative integer | `-123` |
| Decimal number | `1.234` |
| Small decimal | `-1.23` |

Very large or very small values may not fit on the display.

In the CodyNick Python library, values outside the normal display range are treated as out of range.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Example: Count Up</h2>

This example counts from `0` to `9`.

```python
import CodyNick
import time

cn = CodyNick.CN()

for number in range(10):
    CodyNick.Seven_Segment.display(cn, "Stand-Alone", number)
    time.sleep(0.5)
```

The number changes every half second.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Example: Countdown</h2>

This example counts down from `5` to `0`.

```python
import CodyNick
import time

cn = CodyNick.CN()

for number in range(5, -1, -1):
    CodyNick.Seven_Segment.display(cn, "Stand-Alone", number)
    time.sleep(1)
```

The third value in `range(5, -1, -1)` means the loop counts down by `1`.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Example: Show Decimal Values</h2>

This example displays a few decimal values.

```python
import CodyNick
import time

cn = CodyNick.CN()

values = [1.234, 2.5, 3.75, -1.23]

for value in values:
    CodyNick.Seven_Segment.display(cn, "UltraSeg", value)
    time.sleep(1)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Function Summary</h2>

| Function | Purpose | Example |
|---|---|---|
| `Seven_Segment.display(cn, device, value)` | Display a number | `display(cn, "Stand-Alone", 1234)` |

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Practice Tasks</h2>

Try these exercises:

1. Display `1234`.
2. Display `-123`.
3. Display `1.234`.
4. Count from `0` to `9`.
5. Count down from `9` to `0`.
6. Display a list of decimal values.
7. Create a timer that counts seconds.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Common Mistakes</h2>

The first argument must be the connected CodyNick device:

```python
CodyNick.Seven_Segment.display(cn, "Stand-Alone", 1234)
```

This is not correct:

```python
CodyNick.Seven_Segment.display(cn, 1234)
```

If a value is too long, it may not appear as expected on the display.

Use short numeric values:

```python
CodyNick.Seven_Segment.display(cn, "Stand-Alone", 1234)
```

When using a loop, add a delay so each value can be seen:

```python
time.sleep(0.5)
```

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Page summary:</strong><br>
Seven-segment display gadgets show short numeric values. Use `Seven_Segment.display(cn, device, value)` to choose either the stand-alone display or the display inside UltraSeg.
</div>
