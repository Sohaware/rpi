# Your First Gadget Program

This program connects to CodyNick, turns the RGB matrix green for two seconds, and
then switches it off.

```python
import time
import CodyNick

cody = CodyNick.CN()
try:
    if not cody.ensure_connected():
        raise RuntimeError("Connect the CodyNick gadget and try again.")

    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, "#00FF00")
    time.sleep(2)
finally:
    try:
        CodyNick.RGB_Matrix.clear(cody)
    finally:
        cody.close()
```

Use `try` and `finally` around hardware code. Cleanup then runs after a normal finish,
an error, or an IDE stop request.

