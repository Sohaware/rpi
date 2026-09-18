# Motion Detection

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Purpose Of This Page</h2>

This page explains how to read the Motion Detection gadget using Python.

The motion detector reports whether motion is currently detected or not detected.

By the end of this page, students will be able to:

- Read the motion detector.
- Use `True` and `False` results in a Python program.
- Print a message only when motion first appears.

<img src="https://dl.sohaware.com/uploads/projects/codynick/img/motion.JPG" alt="Motion Detection sensor" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 1 - Motion Detection sensor gadget.
</div>

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Start Code</h2>

Every CodyNick Python script should import the CodyNick library and connect to the CodyNick device.

```python
import CodyNick

cn = CodyNick.CN()
```

The variable `cn` represents the connected CodyNick device.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Read Motion</h2>

Use `Motion_Detection.detect()` to check whether motion is detected.

Function format:

```python
CodyNick.Motion_Detection.detect(cn)
```

This function returns:

| Result | Meaning |
|---|---|
| `True` | Motion is detected |
| `False` | No motion is detected |

Example:

```python
import CodyNick

cn = CodyNick.CN()

if CodyNick.Motion_Detection.detect(cn):
    print("motion detected")
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Example: Check Continuously</h2>

```python
import CodyNick
import time

cn = CodyNick.CN()

while True:
    if CodyNick.Motion_Detection.detect(cn):
        print("motion detected")
    else:
        print("no motion")

    time.sleep(0.2)
```

The short delay slows the loop down so the terminal stays readable.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Example: Print Only When Motion Starts</h2>

```python
import CodyNick
import time

cn = CodyNick.CN()
last_motion = False

while True:
    motion = CodyNick.Motion_Detection.detect(cn)

    if motion and not last_motion:
        print("motion started")

    last_motion = motion
    time.sleep(0.1)
```

The variable `last_motion` remembers the previous reading. This prevents the same motion event from being printed many times.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Function Summary</h2>

| Function | Purpose | Example |
|---|---|---|
| `Motion_Detection.detect(cn)` | Check whether motion is detected | `if Motion_Detection.detect(cn):` |

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Practice Tasks</h2>

1. Print `motion` when movement is detected.
2. Print `still` when no movement is detected.
3. Print a message only when motion first starts.
4. Count how many separate motion events occur.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Common Mistakes</h2>

`detect()` returns a Boolean value. Use it directly inside `if`:

```python
if CodyNick.Motion_Detection.detect(cn):
    print("motion detected")
```

Do not compare the result to text such as `"yes"` or `"motion"`.

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Page summary:</strong><br>
Use `Motion_Detection.detect(cn)` when a program needs to know whether motion is present. The result is either `True` or `False`.
</div>
