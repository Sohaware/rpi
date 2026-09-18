<a id="top"></a>
# CodyNick Python Quick Reference

<style>
html {
  scroll-behavior: smooth;
}
</style>

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Contents</h2>

| Section | Main Commands |
|---|---|
| [Start Code](#start-code) | `CodyNick.CN()` |
| [RGB LED Matrix](#rgb-led-matrix) | `set`, `set_xy`, `clear` |
| [Joystick](#joystick) | `position`, `click`, `states` |
| [LED Matrix](#led-matrix) | `display_text`, `set_pixel`, `on`, `off`, `clear` |
| [CJP Sound Maker](#cjp-sound-maker) | `play`, `play_until_done` |
| [Seven Segment Display](#seven-segment-display) | `display` |
| [Motion Detection](#motion-detection) | `detect` |
| [Temperature Sensor](#temperature-sensor) | `read` |
| [Ultrasonic Sensor](#ultrasonic-sensor) | `read` |
| [Connection Control](#connection-control) | `close` |

<a id="start-code"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Start Code <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

```python
import CodyNick

cn = CodyNick.CN()
```

`cn` is the connected CodyNick device object. Pass it as the first argument to CodyNick hardware functions.

<a id="rgb-led-matrix"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">RGB LED Matrix <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Set One LED By Number

```python
CodyNick.RGB_Matrix.set(cn, led, color)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `led` | LED number from `0` to `15` |
| `color` | Color code `0..7`, RGB hex string, or RGB percentage list |

Accepted `color` formats:

```python
0
"#00FFFF"
[0, 100, 100]
```

Examples:

```python
CodyNick.RGB_Matrix.set(cn, 15, 0)
CodyNick.RGB_Matrix.set(cn, 15, "#00FFFF")
CodyNick.RGB_Matrix.set(cn, 15, [0, 100, 100])
```

### Set One LED By Coordinate

```python
CodyNick.RGB_Matrix.set_xy(cn, x, y, color)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `x` | Horizontal coordinate from `0` to `3` |
| `y` | Vertical coordinate from `0` to `3` |
| `color` | Color code `0..7`, RGB hex string, or RGB percentage list |

Coordinate system:

```text
(0,3)  (1,3)  (2,3)  (3,3)
(0,2)  (1,2)  (2,2)  (3,2)
(0,1)  (1,1)  (2,1)  (3,1)
(0,0)  (1,0)  (2,0)  (3,0)
```

Example:

```python
CodyNick.RGB_Matrix.set_xy(cn, 0, 0, "#FF0000")
```

### Clear All RGB LEDs

```python
CodyNick.RGB_Matrix.clear(cn)
```

Turns off all RGB LEDs.

### Built-In Color Codes

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

<a id="joystick"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Joystick <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Check One Direction

```python
CodyNick.Joystick.position(cn, device, direction)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `device` | `"CJP"`, `"Stand-Alone"`, or a supported joystick code |
| `direction` | `"up"`, `"down"`, `"left"`, or `"right"` |

Returns `True` or `False`.

Example:

```python
if CodyNick.Joystick.position(cn, "CJP", "up"):
    print("up")
```

### Check Button Click

```python
CodyNick.Joystick.click(cn, device)
```

Returns `True` when the joystick button is pressed.

### Read All Current States

```python
CodyNick.Joystick.states(cn, device)
```

Returns a list such as:

```python
[]
["UP"]
["LEFT"]
["CLICK"]
["UP", "LEFT", "CLICK"]
```

Example:

```python
states = CodyNick.Joystick.states(cn, "Stand-Alone")
```

<a id="led-matrix"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">LED Matrix <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Display Scrolling Text

```python
CodyNick.LED_Matrix.display_text(cn, text, speed)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `text` | ASCII text to display |
| `speed` | `0`, `1`, `2`, `"slow"`, `"medium"`, or `"fast"` |

Examples:

```python
CodyNick.LED_Matrix.display_text(cn, "Hello", "slow")
CodyNick.LED_Matrix.display_text(cn, "CodyPy", 2)
```

### Set One Pixel

```python
CodyNick.LED_Matrix.set_pixel(cn, x, y, state)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `x` | Horizontal coordinate from `0` to `7` |
| `y` | Vertical coordinate from `0` to `7` |
| `state` | `1` / `True` for on, `0` / `False` for off |

Example:

```python
CodyNick.LED_Matrix.set_pixel(cn, 3, 4, 1)
```

### Turn One Pixel On

```python
CodyNick.LED_Matrix.on(cn, x, y)
```

Example:

```python
CodyNick.LED_Matrix.on(cn, 3, 4)
```

### Turn One Pixel Off

```python
CodyNick.LED_Matrix.off(cn, x, y)
```

Example:

```python
CodyNick.LED_Matrix.off(cn, 3, 4)
```

### Clear The Matrix

```python
CodyNick.LED_Matrix.clear(cn)
```

<a id="cjp-sound-maker"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">CJP Sound Maker <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Play A Note And Continue

```python
CodyNick.CJP_Sound_Maker.play(cn, note, duration_ms)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `note` | Musical note from `B0` to `D#8`, such as `"C4"`, `"F#2"`, or `"Gb2"` |
| `duration_ms` | Duration in milliseconds |

Example:

```python
CodyNick.CJP_Sound_Maker.play(cn, "F#2", 300)
```

### Play A Note And Wait Until Done

```python
CodyNick.CJP_Sound_Maker.play_until_done(cn, note, duration_ms)
```

Same parameters as `play()`, but Python waits until the note is finished.

Example:

```python
CodyNick.CJP_Sound_Maker.play_until_done(cn, "C4", 500)
```

<a id="seven-segment-display"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Seven Segment Display <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Display A Number

```python
CodyNick.Seven_Segment.display(cn, device, value)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `device` | `"Stand-Alone"` or `"UltraSeg"` |
| `value` | Number or numeric string to show |

Examples:

```python
CodyNick.Seven_Segment.display(cn, "Stand-Alone", 1234)
CodyNick.Seven_Segment.display(cn, "Stand-Alone", -123)
CodyNick.Seven_Segment.display(cn, "UltraSeg", 1.234)
```

<a id="motion-detection"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Motion Detection <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Detect Motion

```python
CodyNick.Motion_Detection.detect(cn)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |

Returns:

```python
True
False
```

Example:

```python
if CodyNick.Motion_Detection.detect(cn):
    print("motion detected")
```

<a id="temperature-sensor"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Temperature Sensor <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Read Temperature

```python
CodyNick.Temperature_Sensor.read(cn)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |

Returns temperature in Celsius, such as:

```python
24.6
```

Example:

```python
temperature = CodyNick.Temperature_Sensor.read(cn)
```

<a id="ultrasonic-sensor"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Ultrasonic Sensor <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Read Distance

```python
CodyNick.Ultrasonic_Sensor.read(cn, device)
```

| Parameter | Description |
|---|---|
| `cn` | Connected CodyNick device |
| `device` | `"Stand-Alone"` or `"UltraSeg"` |

Returns distance in centimeters, such as:

```python
37.4
```

Example:

```python
distance = CodyNick.Ultrasonic_Sensor.read(cn, "UltraSeg")
```

<a id="connection-control"></a>
<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Connection Control <span style="font-size:0.72em; font-weight:normal;"><a href="#top">Go to top</a></span></h2>

### Close The Connection

```python
cn.close()
```

Closes the serial connection to the CodyNick device.

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Quick summary:</strong><br>
Use `RGB_Matrix` for RGB LEDs, `Joystick` for joystick input, `CJP_Sound_Maker` for notes, `Seven_Segment` for numeric output, `Motion_Detection` for PIR motion sensing, `Temperature_Sensor` for Celsius readings, and `Ultrasonic_Sensor` for distance in centimeters.
</div>
