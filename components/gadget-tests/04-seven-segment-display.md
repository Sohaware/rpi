# Stand-Alone Seven-Segment Display Test

The display should count from 1 through 10.

```python
import time
import CodyNick

cody = CodyNick.CN()

for number in range(1, 11):
    CodyNick.Seven_Segment.display(cody, "Stand-Alone", number)
    time.sleep(0.5)
```

Use the exact device name `"Stand-Alone"`. The last number remains visible after the
program finishes.
