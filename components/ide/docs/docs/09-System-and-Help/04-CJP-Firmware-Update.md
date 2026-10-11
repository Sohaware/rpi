# Update CodyJoy Pro Firmware from a HEX File

CodyJoy Pro (CJP) is the USB gateway between the Raspberry Pi and CodyNick gadgets. The Raspberry Pi installer does not flash CJP automatically; firmware programming is a separate, deliberate operation.

## Before You Start

You need a verified ATmega328P firmware file such as `/home/admin/CodyPi.hex`. Connect one CJP by USB and do not remove USB power while programming.

## 1. Show the Device Code and Hotspot Name

```bash
serial=$(tr -d '\0\n' </sys/firmware/devicetree/base/serial-number); echo "${serial: -8}"
```

```bash
serial=$(tr -d '\0\n' </sys/firmware/devicetree/base/serial-number); echo "codynick-${serial: -8}"
```

## 2. Install AVRDUDE

```bash
sudo apt-get update && sudo apt-get install -y avrdude
```

## 3. Check the Firmware File

```bash
ls -l /home/admin/CodyPi.hex
```

Stop if the file is missing or empty.

## 4. Find the Serial Port

```bash
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

A CH340-based CJP normally appears as `/dev/ttyUSB0`; an original Arduino Uno interface normally appears as `/dev/ttyACM0`. Replace the port in later commands when necessary.

## 5. Stop CodyNick Serial Services

```bash
sudo systemctl stop codynick.service script.service
```

## 6. Test the Bootloader

```bash
sudo avrdude -v -p atmega328p -c arduino -P /dev/ttyUSB0 -b 115200
```

A correct connection reports device signature `0x1e950f`. An older compatible bootloader may require `-b 57600`.

## 7. Program and Verify

```bash
sudo avrdude -v -p atmega328p -c arduino -P /dev/ttyUSB0 -b 115200 -D -U flash:w:/home/admin/CodyPi.hex:i
```

Confirm that AVRDUDE reports both writing and verifying flash without an earlier error. The final `avrdude done` line alone does not prove success.

## 8. Restore CodyNick Services

```bash
sudo systemctl start codynick.service
```

```bash
sudo systemctl start script.service
```

```bash
sudo systemctl status codynick.service script.service --no-pager
```

The watchdog should be active. The student-script service can fail when `active_script.py` itself contains an error. If these services were disabled rather than stopped, enable them again:

```bash
sudo systemctl enable codynick.service script.service
```

## Optional Direct Serial Access

Programming with `sudo` works immediately. To give `admin` direct serial access:

```bash
sudo usermod -aG dialout admin
```

Log out and reconnect before checking that `groups` includes `dialout`.

## Troubleshooting

- **Permission denied:** use `sudo`, or reconnect after adding `admin` to `dialout`.
- **Device or resource busy:** stop `codynick.service` and `script.service`.
- **Programmer not responding:** verify the port, USB cable, power, board type, and baud rate.
- **Unexpected device signature:** stop and confirm the selected device is an ATmega328P-based CJP.
