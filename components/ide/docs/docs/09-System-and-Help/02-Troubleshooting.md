# Troubleshooting

## The script does not restart

Select **Run This File** and watch the live terminal. A syntax error can make the new
process exit immediately. Save a genuine content change so the watchdog detects it.

## Serial permission denied

Run the unified setup command again. It repairs the `client` account's device-group
membership. A login session created before the repair may need to be restarted.

## Webcam remains active

Current one-shot captures release the camera automatically. Find any process still
using a video device:

```bash
sudo fuser -v /dev/video*
```

Stop the current student script if it owns the device:

```bash
sudo systemctl stop script.service
```

Use `try/finally`, `ai.close_camera()`, and `ai.close()` in custom camera loops.

## No upstream internet

The built-in `wlan0` should serve the Pi hotspot at `10.42.0.1`. Ethernet or a USB
Wi-Fi interface beginning with `wlx` should provide internet. A 2.4 GHz-only dongle
cannot see a 5 GHz-only phone hotspot.

## Installation status

```bash
sudo systemctl status codynick-install --no-pager
```

```bash
sudo journalctl -u codynick-install -n 100 --no-pager
```
