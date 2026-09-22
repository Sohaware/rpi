# Ultrasonic Sensor

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Purpose Of This Page</h2>

This page explains how to read ultrasonic distance gadgets using Python.

The ultrasonic sensor measures distance in centimeters.

By the end of this page, students will be able to:

- Read the current distance.
- Print a value with its unit.
- Use distance inside a simple condition.

<img src="/docs/assets/gadgets/ultrasonic.jpg" alt="Ultrasonic sensor" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 1 - Ultrasonic Sensor gadget.
</div>

<img src="/docs/assets/gadgets/ultraseg.png" alt="UltraSeg gadget" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 2 - UltraSeg gadget. It combines an ultrasonic sensor with a seven-segment display.
</div>

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Start Code</h2>

```python
import CodyNick

cn = CodyNick.CN()
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Choose The Sensor Device</h2>

Every ultrasonic sensor command needs a device name.

| Device name | Meaning |
|---|---|
| `"Stand-Alone"` | Separate ultrasonic sensor gadget |
| `"UltraSeg"` | Ultrasonic sensor inside UltraSeg |

Names are flexible. For example, `"stand-alone"`, `"standalone"`, `"stand alone"`, `"ultraseg"`, and `"ultra-seg"` also work.

Python returns distance in centimeters for both devices. UltraSeg measures internally in millimeters, but the library converts the reading before returning it.

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Read Distance</h2>

Use `Ultrasonic_Sensor.read()` to get the current distance.

Function format:

```python
CodyNick.Ultrasonic_Sensor.read(cn, device)
```

The result is a distance in centimeters, such as:

```python
37.4
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

distance = CodyNick.Ultrasonic_Sensor.read(cn, "Stand-Alone")
print(distance)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Example: Print With A Unit</h2>

```python
import CodyNick

cn = CodyNick.CN()

distance = CodyNick.Ultrasonic_Sensor.read(cn, "UltraSeg")
print("Distance:", distance, "cm")
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Example: Detect A Nearby Object</h2>

```python
import CodyNick
import time

cn = CodyNick.CN()

while True:
    distance = CodyNick.Ultrasonic_Sensor.read(cn, "Stand-Alone")

    if distance is not None and distance < 20:
        print("Object is nearby")

    time.sleep(0.2)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Function Summary</h2>

| Function | Purpose | Unit |
|---|---|---|
| `Ultrasonic_Sensor.read(cn, device)` | Read current distance | Centimeters |

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Practice Tasks</h2>

1. Print the current distance once.
2. Print the distance with the text `cm`.
3. Print `near` when the distance is below `20 cm`.
4. Print `far` when the distance is above `100 cm`.
5. Display distance on a seven-segment display.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Common Mistakes</h2>

Distance is returned in centimeters, not meters:

```python
distance = CodyNick.Ultrasonic_Sensor.read(cn, "Stand-Alone")
```

In larger programs, check that the result is not `None` before comparing it:

```python
if distance is not None and distance < 20:
    print("near")
```

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Page summary:</strong><br>
Use `Ultrasonic_Sensor.read(cn, device)` to read distance in centimeters from either the stand-alone sensor or UltraSeg. The result is a numeric value such as `37.4`.
</div>
