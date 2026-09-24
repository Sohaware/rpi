# Soil-Moisture Sensor Test

Compare a dry sample with a damp soil sample.

```python
import time
import CodyNick

cody = CodyNick.CN()

while True:
    moisture = CodyNick.Soil_Moisture_Sensor.read(cody)
    print("Soil moisture:", moisture)
    time.sleep(1)
```

The reading should change clearly between dry and damp conditions. Keep the connector
and controller electronics dry.
