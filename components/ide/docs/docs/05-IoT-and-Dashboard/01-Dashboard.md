# IoT Dashboard

Open `http://10.42.0.1/dashboard/`. Python programs can create cards backed by the
local MariaDB database. Available card types include indicators, gauges, text,
buttons, switches, sliders, graphs, tables, bar charts, and pie charts.

The browser refreshes card values periodically. Interactive controls write their new
value to the database; the Python program must call `sync()` to receive it.

```python
import time
from Dashboard import Card

temperature = Card("gauge", "Temperature", value=22)
switch = Card("switch", "Fan", value=False)

while True:
    switch.sync()
    temperature.set(23.5)
    time.sleep(1)
```

Keep the dashboard on the trusted CodyNick network. It is a classroom/local-network
tool and is not designed to be exposed directly to the public internet.

For reliable projects, treat browser controls as requests and sensor values as device
reports. Avoid having the browser and Python repeatedly overwrite the same value for
different purposes.

