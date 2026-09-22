# CodyNick Controller Wi-Fi and IoT

`WiFi_IoT` is a static class; do not instantiate it.

```python
import CodyNick

cody = CodyNick.CN()
if not cody.ensure_connected():
    raise RuntimeError("CodyNick controller not found")
```

## Store connection fields

```python
CodyNick.WiFi_IoT.set_ssid(cody, ssid)              # -> bool
CodyNick.WiFi_IoT.set_password(cody, password)      # -> bool
CodyNick.WiFi_IoT.set_cloud_mode(cody, mode)        # -> bool
CodyNick.WiFi_IoT.set_username(cody, username)      # -> bool
CodyNick.WiFi_IoT.set_device_id(cody, device_id)    # -> bool
CodyNick.WiFi_IoT.set_device_key(cody, device_key)  # -> bool
```

Each value must be ASCII and at most 40 characters. `False` means the command was
invalid, the controller was unavailable, or it did not acknowledge the field.

Convenience calls:

```python
wifi_ok = CodyNick.WiFi_IoT.set_wifi(cody, ssid, password)
iot_ok = CodyNick.WiFi_IoT.set_iot(
    cody, username, device_id, device_key, cloud_mode=1
)
```

Each returns `True` only when every included field was acknowledged.

## Restart/reset commands

```python
CodyNick.WiFi_IoT.restart(cody)     # reset the external module
CodyNick.WiFi_IoT.reset_wifi(cody)  # restart Wi-Fi connection
CodyNick.WiFi_IoT.reset_iot(cody)   # restart cloud connection
```

All return `bool`. A successful return means the reset request was accepted, not that
the connection is already online.

## Connection status

```python
state = CodyNick.WiFi_IoT.status(cody)
# {"wifi": integer_status, "iot": integer_status} or None

wifi_code = CodyNick.WiFi_IoT.wifi_status(cody)
iot_code = CodyNick.WiFi_IoT.iot_status(cody)
wifi_ready = CodyNick.WiFi_IoT.wifi_connected(cody)  # wifi code == 3
iot_ready = CodyNick.WiFi_IoT.iot_connected(cody)    # iot code == 1
```

Use the boolean helpers unless the controller firmware's numeric status codes are
specifically needed.

## Read stored fields

```python
CodyNick.WiFi_IoT.get_wifi_ssid(cody)
CodyNick.WiFi_IoT.get_wifi_password(cody)
CodyNick.WiFi_IoT.get_device_id(cody)
CodyNick.WiFi_IoT.get_device_key(cody)
CodyNick.WiFi_IoT.get_username(cody)
CodyNick.WiFi_IoT.get_esp_version(cody)
CodyNick.WiFi_IoT.get_stm_version(cody)
CodyNick.WiFi_IoT.get_lib_version(cody)
```

Each returns a string or `None`. Do not print passwords or device keys in student logs.
They are convenience wrappers around:

```python
value = CodyNick.WiFi_IoT.credential_state(cody, step)
```

`step` values `0..7` select SSID, password, device ID, device key, username, ESP
version, STM version, and library version respectively. Prefer the named getters.

## Keep-alive helpers

```python
wifi_ready = CodyNick.WiFi_IoT.keep_alive_wifi(
    cody, ssid, password, Trst=15, Tchk=10, Tstartup=10
)

iot_ready = CodyNick.WiFi_IoT.keep_alive_iot(
    cody, username, device_id, device_key,
    cloud_mode=1, Trst=15, Tchk=10, Tstartup=10
)
```

- `Tstartup`: wait after serial connection before configuring the module.
- `Tchk`: minimum seconds between stored-credential checks.
- `Trst`: minimum seconds between reset attempts.
- Return `True` only when the requested connection is currently established.

Call these repeatedly from a paced loop. They update changed credentials and request
resets when needed; they are not blocking connection functions.
