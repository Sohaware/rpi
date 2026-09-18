# CodyNick Raspberry Pi installation

## Current version

**Network: v0.1.2-network. Core applications: v0.2.0-core (first-device trial).**
Both stages target Ubuntu Server 26.04 ARM64. The network-only trial supports
on Raspberry Pi 5. Repeated fresh-install tests, hotspot/SSH access, internet sharing,
and reboot persistence passed on the tested Pi with a Realtek RTL8188EUS USB dongle.

The network stage does not install applications. After completing it, use section 6
to install the IDE, CodyNick library, dashboard, and script services. AI environments
and models are a separate, not-yet-published stage; chapter 8 remains reserved for a
later upgrade. Ethernet-only operation, other adapters, and broader failure recovery
still need validation. Do not treat this as a production fleet updater yet.

## 1. Prepare before installation

Before powering on the Pi for setup, prepare an external router or phone hotspot:

| Setting | Value |
| --- | --- |
| External internet Wi-Fi SSID | `codynick` |
| External internet Wi-Fi password | `codynick` |

Keep this network powered on and connected to the internet throughout installation.
For the tested RTL8188EUS adapter, make a 2.4 GHz network available. This external
network is different from the hotspot the Pi will create.

In Raspberry Pi Imager, write **Ubuntu Server 26.04 ARM64** and configure:

- An administrator account (examples use `admin`) and password or SSH key.
- SSH access.
- Built-in Wi-Fi to join `codynick` with password `codynick`.
- The Wi-Fi country appropriate to the Pi's physical location.

Connect the USB Wi-Fi dongle before booting. Ethernet with internet access is also
supported as an alternative uplink. Do not configure the dongle manually.
Keep local terminal access available for recovery during this trial.

## 2. Complete first boot, then reboot

Allow Ubuntu's first-boot initialization to finish.

**Reboot before running the CodyNick installer or doing any other setup.** On the tested
image, built-in Wi-Fi does not reliably connect to `codynick` until this reboot.
Do not power off while first-boot initialization is still running.

From the local terminal, or SSH if already available:

```bash
sudo reboot
```

After reboot, log in locally or connect through MobaXterm using the Pi's address on
the external network, your administrator account, and port 22. Find the address in
the router's client list, or display it locally:

```bash
hostname -I
```

This initial DHCP address can change. Do not assume it matches a previous SD card.

## 3. Download and run

```bash
wget -O /tmp/codynick-setup.sh https://raw.githubusercontent.com/Sohaware/rpi/v0.1.2-network/bootstrap/codynick-setup.sh
```

```bash
sudo bash /tmp/codynick-setup.sh
```

Check that the banner says **0.1.2**. Answer `y` to
`Prepare this network handover? [y/N]`.

The installer installs prerequisites, detects adapters, and verifies HTTPS internet
through Ethernet or the dongle before switching built-in Wi-Fi. Ethernet is preferred
when both uplinks are available.

At `Switch to the hotspot now? [y/N]`, record the displayed hotspot name and answer
`y`. Your existing SSH connection will disconnect during this deliberate switch.

## 4. Join the hotspot and confirm

| Setting | Value |
| --- | --- |
| Pi hotspot SSID | `codynick-` plus the last eight hardware serial digits |
| Example SSID | `codynick-d82c57b4` |
| Pi hotspot password | `CodyNick12345` |
| Pi hotspot/SSH address | `10.42.0.1` |
| SSH username | Your existing administrator, such as `admin` |
| SSH authentication | Your existing administrator password or key |

Connect your computer to this hotspot. Open MobaXterm SSH to `10.42.0.1`, or run
this on your computer (substitute your username if different):

```bash
ssh admin@10.42.0.1
```

From that SSH session, confirm within **15 minutes**:

```bash
sudo codynick-setup --confirm
```

Answer `y`. Success reports `Stage: network-ready` and disables rollback.
This release still requires explicit `--confirm`. No root password is set.

Without confirmation, the timer is intended to restore the previous network.
A reboot before confirmation restarts its 15-minute interval. The original
router-assigned IP address may change after restoration.

## 5. Verify after reboot

After confirmation:

```bash
sudo reboot
```

Reconnect to the same hotspot and SSH at `10.42.0.1`, then run:

```bash
sudo codynick-setup --check
```

Expected results:

- `Stage: network-ready`.
- Built-in Wi-Fi has `10.42.0.1/24`.
- The dongle has an external address and route metric `200` when used.
- `ssh`, `codynick-ap.service`, `codynick-dhcp.service`, and `codynick-nat.service` are active.
- Your computer can browse the internet through the Pi hotspot.

Ethernet can show `DOWN` without a cable. Changes in the dongle's DHCP address are
normal; the hotspot address remains `10.42.0.1`.

**Keep this SD card.** Network setup is complete. Rerunning this version reports
status; it does not install the IDE or AI tools. Continue below.

## 6. Install core applications

**Already connected to the verified hotspot? Start here. Do not rewrite the SD card
or repeat the network handover.** Keep the external internet network available.

Run these commands in the Pi's existing administrator SSH session at `10.42.0.1`:

```bash
wget -O /tmp/codynick-apps.sh https://raw.githubusercontent.com/Sohaware/rpi/v0.2.0-core/bootstrap/codynick-apps.sh
```

```bash
sudo bash /tmp/codynick-apps.sh
```

```bash
sudo journalctl -fu codynick-install
```

Installation runs in the background, so closing SSH does not stop it. Do not reboot
or power off until it finishes. Wait for **`CodyNick core 0.2.0: READY`**, then press
`Ctrl+C` to leave the log display. If you see `INSTALLATION FAILED`, send the last
30-50 log lines for diagnosis; do not continue as though installation succeeded.

Open [Python IDE](http://10.42.0.1/code/) in your computer's browser. Create a file,
paste this test, and click **Run this File**:

```python
import time
for number in range(10):
    print("CodyNick test", number, flush=True)
    time.sleep(1)
```

The terminal under the editor should receive one line per second. Click Run again
while it is running: output should restart from zero. Also open the
[dashboard](http://10.42.0.1/dashboard/) and [block editor](http://10.42.0.1/blocks/).
Some editor assets currently use external CDNs, so keep internet access available.

### Installed scope and credentials

| Item | Details |
| --- | --- |
| Web applications | `/var/www/html`: Python IDE/live log, Blockly, dashboard, documentation |
| Python libraries and student code | `/home/client`; CodyNick.py 1.20.1 and Dashboard.py |
| Script watcher | `/root/codynick`, `codynick.service` |
| Student script execution | `script.service`, runs as `client`, unbuffered output to `/home/client/log.log` |
| Isolated core Python | `/opt/codynick/core-0.2.0/bin/python`; keyboard, PySerial, requests, MySQL connector |
| SSH administrator | Existing username/password or key, unchanged |
| New client account | `client` / `codynick`; existing account passwords are not reset |
| Dashboard database | Database/user/password: `codynick` / `codynick` / `codynick`; database-scoped permissions |
| Root login/password | Unchanged; root login is not required |
| AI environments/models | **Not installed in this core release** |

This is a trusted-classroom-network application, not an internet-facing service.
The IDE does not provide user authentication or isolate students from one another.
Do not forward its web or SSH ports to the internet. Change default account passwords
before deployment outside a controlled classroom. Installing `keyboard` fixes its
import; Linux keyboard-hook operations may still require privileges and are not
validated by the import check.

### Repeating, checking, and recovering

Repeat the same download/run commands to retry or repair **this core version**. It
rechecks dependencies and redeploys managed application files. It preserves saved
Python files, active_script.py, media, logs, dashboard records, web configuration,
saved Blockly arrangements/packages, and existing account passwords. The running
student script is restarted during installation.

No OS-wide upgrade, reboot, root-password reset, or network reconfiguration is
performed. A legacy application installation or a different application version is
refused rather than blindly overwritten. Migration from future/other versions is
not yet implemented. Edited managed source files are backed up before replacement;
this is not a full-system/database backup or transactional rollback. Back up important
student data separately before any deployment.

To view the installed component versions and run health checks:

```bash
sudo python3 /usr/local/lib/codynick/core-0.2.0/app_setup.py --check
```

To retrieve the latest installation output after reconnecting:

```bash
sudo journalctl -u codynick-install -n 50 --no-pager
```

State is stored in `/var/lib/codynick/application-state.json`. Only a successful
health check records `stage: ready`. Backups of replaced payload files are under
`/var/backups/codynick/core-*`. Interrupted installations can leave partially updated
applications; rerun this same release after addressing the reported error. Installation
does not automatically resume after a power failure/reboot. The verified hotspot
configuration is left untouched.

## Version history

| Version | Status | What is new |
| --- | --- | --- |
| **0.2.0-core** | First application trial; Pi installation/user acceptance pending | Adds detached, checksummed core installation, isolated Python dependencies, Apache/PHP/MariaDB, client permissions, script/watchdog services, health checks, and repeat-install data preservation. Corrects Blockly output path and repeat-run detection. No AI models or environment deployment yet. |
| **0.1.2** | Current network trial; fresh-install and reboot tests passed on the tested hardware | Corrects inherited file-creation permissions so networkd can read generated Netplan files. Fixes the fallback networking and unintended DHCP address changes caused by unreadable files. |
| 0.1.1 | Superseded; do not install | Reuses a correct working dongle profile, targets USB preparation instead of global Netplan application, arms rollback earlier, and retries recovery. Fresh-install testing subsequently found the permissions defect fixed in 0.1.2. |
| 0.1.0 | Superseded; do not install | Introduced adapter detection, internet checks, hotspot handover, confirmation, rollback, and version/state reporting. Global Netplan application could disconnect SSH during preparation. |

The core application stage does not change the network installer version 0.1.2.
See [CHANGELOG.md](CHANGELOG.md) for technical details.

**For every future published version**, update this table, current-version section,
download URL, prerequisites, tested scope, and changelog. Explain what changed and
any required user action. Keep published tags unchanged; fixes receive new versions.

## Recovery

Recover interrupted old attempts before installing again. Do not delete the setup lock
file: its owner must release it. Recovery can disconnect SSH as original networking
returns; use local access or a recovery process independent of SSH.

From a local terminal:

```bash
sudo codynick-setup --rollback
```

If it reports `Resource temporarily unavailable`, identify the other setup process
before stopping it. Backups are stored under `/var/backups/codynick/`.

## Next stage

1. Validate core 0.2.0 on the network-ready Pi: installation, live output, rerun,
   dashboard, hardware access, reboot, and repeat installation without data loss.
2. Package the image's matching AI environments/models for object detection, OCR,
   speech recognition, and speech generation; retain existing on-device paths.
3. Add verified migrations and recovery for later releases, then test the complete
   clean-OS procedure before recommending fleet-wide upgrades.

Chapter 8 will be a separate upgrade. Keep this SD card for the next stage.

## Implementation and testing

- Retains systemd-networkd; does not introduce NetworkManager.
- Uses detected Wi-Fi interface names; networkd Netplan Wi-Fi does not accept `match`.
- Ethernet route metric: `100`; USB metric after handover: `200`.
- Does not flush existing firewall rules. Active UFW requires a reviewed setup.
- Setup state: `/var/lib/codynick/network-setup.json`.
- Disables only cloud-init network generation, not cloud-init itself.
- Keeps credential configuration and backups private on the device.
- Pins a tag and verifies the helper SHA256: HTTPS/checksum integrity, not release signing.

Local tests and GitHub Linux checks passed (17 tests for v0.1.2):

```bash
python -m unittest discover -s tests -v
```

```bash
bash -n bootstrap/codynick-setup.sh
```

Tests cover configuration preservation, interface detection, HTTPS binding, confirmation,
rollback, and subprocess permissions. Hardware results apply to the tested Pi/dongle,
not every adapter or failure scenario.
