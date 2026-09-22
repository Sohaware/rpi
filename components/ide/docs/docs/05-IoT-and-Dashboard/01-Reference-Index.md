# IoT and Dashboard Reference

CodyNick provides two independent IoT interfaces:

1. `Dashboard.py` creates cards in the Pi's local MariaDB-backed browser dashboard.
2. `CodyNick.WiFi_IoT` configures the external CodyNick controller and exchanges four
   typed cloud values through its serial protocol.

## Local dashboard API

```python
import Dashboard

Dashboard.configure(...)
Dashboard.ensure_database()
Dashboard.ensure_table()
Dashboard.clear()

card = Dashboard.Card(...)
card.sync()
card.save()
card.set(...)
card.value_json()
card.delete()
```

See **Dashboard API**, **Card Types**, and **Interactive Patterns**.

## CodyNick controller IoT API

All methods are static and require an existing `CodyNick.CN()` connection:

```python
import CodyNick

cody = CodyNick.CN()
CodyNick.WiFi_IoT.set_wifi(cody, ssid, password)
CodyNick.WiFi_IoT.set_iot(cody, username, device_id, device_key)
CodyNick.WiFi_IoT.write_float(cody, 0, 23.5)
value = CodyNick.WiFi_IoT.read_float(cody, 0)
```

See **Controller Connection** and **Cloud Values**.

