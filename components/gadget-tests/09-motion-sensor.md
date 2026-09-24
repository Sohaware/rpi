# Motion Sensor Test

Keep still, then move a hand or walk in front of the sensor.

```python
import time
import CodyNick

cody = CodyNick.CN()

while True:
    if CodyNick.Motion_Detection.detect(cody):
        print("Motion detected")
    else:
        print("No motion")
    time.sleep(0.5)
```

Some PIR sensors need a short warm-up period after power is connected.
