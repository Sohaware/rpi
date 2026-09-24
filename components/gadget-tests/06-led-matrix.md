# LED Matrix Test

This test shows text, clears the display, and then lights one pixel.

```python
import time
import CodyNick

cody = CodyNick.CN()

CodyNick.LED_Matrix.display_text(cody, "CodyNick", "slow")
time.sleep(4)
CodyNick.LED_Matrix.clear(cody)
CodyNick.LED_Matrix.on(cody, 3, 4)
```

Confirm that the text moves smoothly and the final pixel appears at column 3, row 4.
