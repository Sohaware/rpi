# CodyNick Raspberry Pi deployment

## Current release: 0.1.0 network trial

This first release prepares network access on a fresh Ubuntu 26.04 ARM64 Raspberry Pi 5.
It is NOT yet the complete CodyNick IDE/AI installer or an updater for existing installations.
It does not install chapter 8. Hardware validation on the first Pi is still required.

Keep the current SD card. Log in as the administrator created in Imager (currently `admin`).
Keep the external `codynick` Wi-Fi network available with password `codynick`.
Connect the USB Wi-Fi adapter and/or Ethernet.

Download the versioned bootstrap:

```bash
wget -O /tmp/codynick-setup.sh https://raw.githubusercontent.com/Sohaware/rpi/v0.1.0-network/bootstrap/codynick-setup.sh
```

Run it:

```bash
sudo bash /tmp/codynick-setup.sh
```

It checks Ubuntu/network configuration, installs network prerequisites, detects the USB
adapter, and tests HTTPS through each alternative internet interface. It will not switch
the built-in Wi-Fi without working alternative internet and your explicit confirmation.
Two prompts separate preparation from the actual handover. Country is taken from the
existing Wi-Fi configuration or requested; set it for the physical device location.

Record the hotspot name shown on screen (`codynick-` followed by the last eight hardware
serial digits). Password: `CodyNick12345`. After accepting the switch, join this hotspot.
The current SSH connection will disconnect. No reboot is normally required.

Reconnect (use your existing administrator username if it is not `admin`):

```bash
ssh admin@10.42.0.1
```

Use the SAME administrator password or SSH key as before. No root password is set.
Confirm from the new connection within 15 minutes:

```bash
sudo codynick-setup --confirm
```

Without confirmation, a timer restores the previous network configuration. If the Pi
reboots before confirmation, the timer restarts its 15-minute interval. If connection
fails, wait for restoration and reconnect through the original network. Its DHCP address
may change. A local terminal can trigger restoration immediately:

```bash
sudo codynick-setup --rollback
```

Check status without changing configuration:

```bash
sudo codynick-setup --check
```

After confirmation, the network phase is complete. Application installation follows in
a separate release; rerunning this trial will report status, not install the IDE.

## Implementation

- Existing `/home/client`, `/root/codynick`, and `/var/www/html` layouts will be retained.
- This trial refuses existing CodyNick/hotspot installations rather than overwriting them.
- `systemd-networkd` is retained; NetworkManager is not introduced.
- Netplan uses the detected Wi-Fi interface name (networkd does not accept Wi-Fi `match`).
- Ethernet metric is 100; USB Wi-Fi metric is 200 after handover.
- No existing firewall rules are flushed. Active UFW requires a separate reviewed setup.
- Root-only configuration backups: `/var/backups/codynick/network-*`.
- Version/stage record: `/var/lib/codynick/network-setup.json`.
- Dedicated services: `codynick-ap`, `codynick-dhcp`, `codynick-nat`.
- Logs: `journalctl -u codynick-network-handover -u codynick-ap -u codynick-dhcp`.
- Only cloud-init network generation is disabled; cloud-init itself remains enabled.
- User applications, login credentials, databases, and model files are not copied into Git.

The bootstrap pins a version tag and validates the helper SHA256. This is integrity
checking over HTTPS, not a cryptographic release-signing system. Full signed release
packaging and application install/upgrade/repair remain subsequent work.

## Development validation

```bash
python -m unittest discover -s tests -v
bash -n bootstrap/codynick-setup.sh
```

Tests cover interface detection, preservation of other network definitions, device-bound
HTTPS checks, confirmation safeguards, and backup behavior. They do not substitute for
testing real hostapd, DHCP, SSH, internet sharing, or power interruption on a Pi.
