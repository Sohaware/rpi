# CodyNick Gadgets

The installed `/home/client/CodyNick.py` library provides the gadget API. Begin every
serial gadget program with one shared connection:

```python
import CodyNick

cody = CodyNick.CN()
if not cody.ensure_connected():
    raise RuntimeError("CodyNick gadget not found")
```

Supported interfaces include:

- CodyJoy Pro joystick and buzzer
- 4 by 4 RGB LED matrix
- monochrome LED matrix
- seven-segment display
- temperature, motion, soil moisture, RFID, and ultrasonic sensors
- Wi-Fi and IoT fields supported by the CodyNick controller

Use the detailed pages in the **Python** section for method names and examples. Always
finish with `cody.close()` and clear outputs that should not remain active.

