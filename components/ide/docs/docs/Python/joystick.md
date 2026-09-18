# Joystick

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Purpose Of This Page</h2>

This page explains how to read joystick gadgets using Python.

The CodyJoy Pro includes several built-in features, including:

- RGB LED Matrix.
- Joystick.
- Sound Maker.

This page focuses on the joystick feature. The same Python commands can read the built-in CodyJoy Pro joystick or a stand-alone joystick gadget in the CodyNick chain.

By the end of this page, students will be able to:

- Detect joystick direction.
- Detect joystick button clicks.
- Read all joystick states at once.
- Use joystick input inside a Python loop.

<img src="https://dl.sohaware.com/uploads/projects/codynick/img/cjp_neo.png" alt="CodyJoy Pro with joystick" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 1 - CodyJoy Pro device. The board includes an RGB LED Matrix, joystick, and Sound Maker.
</div>

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Start Code</h2>

Every CodyNick Python script should import the CodyNick library and connect to the CodyNick device.

```python
import CodyNick

cn = CodyNick.CN()
```

The variable `cn` represents the connected CodyNick device.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Choose The Joystick Device</h2>

Every joystick command needs a device name.

| Device name | Meaning |
|---|---|
| `"CJP"` | Joystick built into CodyJoy Pro |
| `"Stand-Alone"` | Stand-alone joystick gadget |

Names are flexible. For example, `"cjp"`, `"stand-alone"`, `"standalone"`, and `"stand alone"` also work.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Joystick Directions</h2>

The joystick can be moved in four main directions:

- Up
- Down
- Left
- Right

The joystick can also be pressed like a button. This is called a click.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Check One Direction</h2>

Use `Joystick.position()` to check one direction.

Function format:

```python
CodyNick.Joystick.position(cn, device, direction)
```

The direction should be one of:

```python
"up"
"down"
"left"
"right"
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

if CodyNick.Joystick.position(cn, "CJP", "up"):
    print("Joystick is up")
```

This prints a message if the joystick is moved up.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Check For A Click</h2>

Use `Joystick.click()` to check whether the joystick button is pressed.

Function format:

```python
CodyNick.Joystick.click(cn, device)
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

if CodyNick.Joystick.click(cn, "Stand-Alone"):
    print("Joystick clicked")
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Read All Joystick States</h2>

Use `Joystick.states()` to read the current joystick state once.

Function format:

```python
CodyNick.Joystick.states(cn, device)
```

This returns a list.

Examples of possible results:

| Result | Meaning |
|---|---|
| `[]` | No direction or click |
| `["UP"]` | Joystick is moved up |
| `["DOWN"]` | Joystick is moved down |
| `["LEFT"]` | Joystick is moved left |
| `["RIGHT"]` | Joystick is moved right |
| `["CLICK"]` | Joystick button is pressed |
| `["UP", "CLICK"]` | Joystick is moved up and clicked |

Example:

```python
import CodyNick

cn = CodyNick.CN()

states = CodyNick.Joystick.states(cn, "CJP")
print(states)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Example: Print Joystick Movement</h2>

This example continuously checks the joystick and prints the direction.

```python
import CodyNick
import time

cn = CodyNick.CN()

while True:
    if CodyNick.Joystick.position(cn, "CJP", "up"):
        print("up")

    if CodyNick.Joystick.position(cn, "CJP", "down"):
        print("down")

    if CodyNick.Joystick.position(cn, "CJP", "left"):
        print("left")

    if CodyNick.Joystick.position(cn, "CJP", "right"):
        print("right")

    if CodyNick.Joystick.click(cn, "CJP"):
        print("click")

    time.sleep(0.1)
```

The `time.sleep(0.1)` line slows the loop down slightly. Without it, Python may print too many messages very quickly.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Example: Read Once Per Loop</h2>

For larger programs, it is often better to read the joystick once per loop using `states()`.

```python
import CodyNick
import time

cn = CodyNick.CN()

while True:
    states = CodyNick.Joystick.states(cn, "Stand-Alone")

    if "UP" in states:
        print("up")
    elif "DOWN" in states:
        print("down")
    elif "LEFT" in states:
        print("left")
    elif "RIGHT" in states:
        print("right")
    elif "CLICK" in states:
        print("click")

    time.sleep(0.1)
```

This style is useful when one program needs to react to different joystick actions.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Example: Count Button Clicks</h2>

This example counts how many times the joystick button is clicked.

```python
import CodyNick
import time

cn = CodyNick.CN()

click_count = 0
was_clicked = False

while True:
    is_clicked = CodyNick.Joystick.click(cn, "CJP")

    if is_clicked and not was_clicked:
        click_count = click_count + 1
        print("Clicks:", click_count)

    was_clicked = is_clicked
    time.sleep(0.05)
```

The variable `was_clicked` helps count one click at a time instead of counting the same press many times.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Function Summary</h2>

| Function | Purpose | Example |
|---|---|---|
| `Joystick.position(cn, device, "up")` | Check if joystick is up | `if Joystick.position(cn, "CJP", "up"):` |
| `Joystick.position(cn, device, "down")` | Check if joystick is down | `if Joystick.position(cn, "CJP", "down"):` |
| `Joystick.position(cn, device, "left")` | Check if joystick is left | `if Joystick.position(cn, "CJP", "left"):` |
| `Joystick.position(cn, device, "right")` | Check if joystick is right | `if Joystick.position(cn, "CJP", "right"):` |
| `Joystick.click(cn, device)` | Check if joystick button is pressed | `if Joystick.click(cn, "Stand-Alone"):` |
| `Joystick.states(cn, device)` | Read all joystick states once | `states = Joystick.states(cn, "CJP")` |

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Practice Tasks</h2>

Try these exercises:

1. Print `up` when the joystick is moved up.
2. Print all four directions when they happen.
3. Print `clicked` when the joystick button is pressed.
4. Count how many times the joystick is clicked.
5. Print the full list returned by `Joystick.states(cn, "CJP")`.
6. Write a program that prints only when the direction changes.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Common Mistakes</h2>

Direction names must be lowercase when using `Joystick.position()`.

Correct:

```python
CodyNick.Joystick.position(cn, "CJP", "up")
```

Not correct:

```python
CodyNick.Joystick.position(cn, "CJP", "UP")
```

The result from `Joystick.states()` uses uppercase state names:

```python
states = CodyNick.Joystick.states(cn, "CJP")

if "UP" in states:
    print("up")
```

If the terminal prints too fast, add a short delay inside the loop:

```python
time.sleep(0.1)
```

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Page summary:</strong><br>
The joystick can be read by checking one direction, checking for a click, or reading all current states at once. Pass a device name such as `"CJP"` or `"Stand-Alone"` so Python knows which joystick to read.
</div>
