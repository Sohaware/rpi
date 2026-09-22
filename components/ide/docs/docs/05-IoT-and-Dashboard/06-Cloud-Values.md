# CodyNick Cloud Values

The external controller exposes indexes `0` through `3`. Each operation supplies the
expected type: `int`, `float`, `bool`, or `string`.

## Generic methods

```python
ok = CodyNick.WiFi_IoT.write(cody, index, value_type, value, verify=False)
value = CodyNick.WiFi_IoT.read(cody, index, value_type)
```

- `index` must be `0..3`.
- `value_type` accepts `int`/`integer`, `float`, `bool`/`boolean`, or `string`/`str`.
- Encoded values must be ASCII and at most 40 characters.
- `write()` returns `bool`; `verify=True` reads the value back before returning.
- `read()` returns the typed value or `None` after invalid input, timeout, or malformed data.
- Every accepted write includes a built-in 0.25 second settling delay.

Float verification allows a difference of `0.01`. String verification compares the
first six characters because of the controller protocol's verification behavior.

## Typed methods

```python
CodyNick.WiFi_IoT.write_int(cody, index, value, verify=False)
CodyNick.WiFi_IoT.write_float(cody, index, value, verify=False)
CodyNick.WiFi_IoT.write_bool(cody, index, value, verify=False)
CodyNick.WiFi_IoT.write_string(cody, index, value, verify=False)

CodyNick.WiFi_IoT.read_int(cody, index)
CodyNick.WiFi_IoT.read_float(cody, index)
CodyNick.WiFi_IoT.read_bool(cody, index)
CodyNick.WiFi_IoT.read_string(cody, index)
```

Prefer the typed methods. They make the intended cloud-variable type visible in code.

## Complete loop

```python
import time
import CodyNick

cody = CodyNick.CN()
try:
    if not cody.ensure_connected():
        raise RuntimeError("Controller not found")

    while True:
        wifi = CodyNick.WiFi_IoT.keep_alive_wifi(
            cody, "network-name", "network-password"
        )
        cloud = wifi and CodyNick.WiFi_IoT.keep_alive_iot(
            cody, "username", "device-id", "device-key"
        )
        if cloud:
            temperature = CodyNick.Temperature_Sensor.read(cody)
            CodyNick.WiFi_IoT.write_float(cody, 0, temperature)
            command = CodyNick.WiFi_IoT.read_string(cody, 1)
            if command is not None:
                print("Cloud command:", command)
        time.sleep(1)
finally:
    cody.close()
```
