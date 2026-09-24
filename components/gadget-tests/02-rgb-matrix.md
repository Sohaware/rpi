# RGB Matrix Test

This test lights all 16 LEDs red, green, blue, and white, then clears the matrix.

```python
import time
import CodyNick

cody = CodyNick.CN()

for color in ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF"]:
    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, color)
    time.sleep(1)

CodyNick.RGB_Matrix.clear(cody)
```

All LEDs should show every color. A consistently missing LED suggests a matrix or
connection fault. Random missed updates suggest an outdated CodyNick library.
