# Temperature Sensor

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Purpose Of This Page</h2>

This page explains how to read the Temperature Sensor gadget using Python.

The sensor returns temperature in degrees Celsius.

By the end of this page, students will be able to:

- Read the current temperature.
- Store a sensor value in a variable.
- Print the value only when it changes.

<img src="/docs/assets/gadgets/temperature.jpg" alt="Temperature sensor" style="max-width:100%; border-radius:10px; margin: 12px 0 24px 0;">
<div style="text-align:center; font-size:0.92em; color:#6b7280; margin-top:-16px; margin-bottom:24px;">
Figure 1 - Temperature Sensor gadget.
</div>

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Start Code</h2>

```python
import CodyNick

cn = CodyNick.CN()
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Read Temperature</h2>

Use `Temperature_Sensor.read()` to get the current temperature.

Function format:

```python
CodyNick.Temperature_Sensor.read(cn)
```

The result is a number in degrees Celsius, such as:

```python
24.6
```

Example:

```python
import CodyNick

cn = CodyNick.CN()

temperature = CodyNick.Temperature_Sensor.read(cn)
print(temperature)
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Example: Print With A Unit</h2>

```python
import CodyNick

cn = CodyNick.CN()

temperature = CodyNick.Temperature_Sensor.read(cn)
print("Temperature:", temperature, "C")
```

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Example: Print Only When The Value Changes</h2>

```python
import CodyNick
import time

cn = CodyNick.CN()
last_temperature = None

while True:
    temperature = CodyNick.Temperature_Sensor.read(cn)

    if temperature is not None and temperature != last_temperature:
        print("Temperature:", temperature, "C")
        last_temperature = temperature

    time.sleep(0.2)
```

`None` means that no valid reading was received at that moment.

<h2 style="font-size: 1.35em; font-weight: bold; color:#d97706;">Function Summary</h2>

| Function | Purpose | Unit |
|---|---|---|
| `Temperature_Sensor.read(cn)` | Read current temperature | Celsius |

<h2 style="font-size: 1.35em; font-weight: bold; color:#16a34a;">Practice Tasks</h2>

1. Print the current temperature once.
2. Print the temperature with the text `C`.
3. Continuously print temperature readings.
4. Print only when the reading changes.
5. Display the temperature on a seven-segment display.

<h2 style="font-size: 1.35em; font-weight: bold; color:#2563eb;">Common Mistakes</h2>

Store the reading before using it:

```python
temperature = CodyNick.Temperature_Sensor.read(cn)
```

If a reading is unavailable, the result can be `None`. Check for that before comparing or displaying the value in larger programs.

<div style="border-left: 5px solid #16a34a; background:#f0fdf4; padding: 12px 16px; border-radius: 8px; margin: 14px 0;">
<strong>Page summary:</strong><br>
Use `Temperature_Sensor.read(cn)` to read temperature in Celsius. The result is a numeric value such as `24.6`.
</div>
