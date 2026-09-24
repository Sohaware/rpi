# Temperature Sensor Test

Hold the sensor at room temperature, then warm it gently and watch the value increase.

```python
import time
import CodyNick

cody = CodyNick.CN()

while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    print("Temperature:", temperature, "C")
    time.sleep(1)
```

The value is degrees Celsius. Do not expose the sensor or its electrical connections
to unsafe temperatures or water unless the sensor assembly is designed for immersion.
