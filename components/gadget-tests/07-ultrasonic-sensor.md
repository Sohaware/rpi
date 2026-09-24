# Ultrasonic Sensor Test

Place a flat object in front of the stand-alone sensor and move it closer and farther.

```python
import time
import CodyNick

cody = CodyNick.CN()

while True:
    distance = CodyNick.Ultrasonic_Sensor.read(cody, "Stand-Alone")
    print("Distance:", distance, "cm")
    time.sleep(0.5)
```

For the sensor built into UltraSeg, replace `"Stand-Alone"` with `"UltraSeg"`.
The reported distance should follow the target without large unexplained jumps.
