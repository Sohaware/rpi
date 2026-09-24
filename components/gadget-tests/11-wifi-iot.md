# Wi-Fi and IoT Module Test

This read-only test reports connection state and module versions without changing
credentials.

```python
import time
import CodyNick

cody = CodyNick.CN()

print("Status:", CodyNick.WiFi_IoT.status(cody))
print("Wi-Fi connected:", CodyNick.WiFi_IoT.wifi_connected(cody))
print("IoT connected:", CodyNick.WiFi_IoT.iot_connected(cody))
print("ESP version:", CodyNick.WiFi_IoT.get_esp_version(cody))
print("STM version:", CodyNick.WiFi_IoT.get_stm_version(cody))
print("Library version:", CodyNick.WiFi_IoT.get_lib_version(cody))
```

Connection booleans should match the module's real state. This test deliberately does
not display saved passwords or modify network/cloud settings.
