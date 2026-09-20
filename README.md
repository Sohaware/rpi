# CodyNick Raspberry Pi installation

## Current version

**Unified setup: 0.5.3; application: 0.5.3 (managed examples polish). Network component: 0.1.2.**
Targets Ubuntu Server 26.04 ARM64 on Raspberry Pi 5. Network setup and core 0.2.2
have passed fresh-OS testing, IDE/run/live-output tests, and a CodyJoy RGB hardware
test. Version 0.3.0 adds USB-camera/object detection and colored terminal output;
USB-camera capture and default-model object detection passed the user's Pi test.
Version 0.4.0 adds the vision demos prepared for 0.3.1 plus offline English
speech-to-text and a microphone-to-RGB voice-command demo; both camera detection and
the voice LED demo passed the user's Pi tests.
Version 0.4.1 fixes same-command confirmation after hotspot handover when sudo
does not retain the SSH connection environment. Version 0.5.0 adds offline English
camera OCR, corrects the `start.codynick` homepage, retries interrupted source/OCR
downloads, and releases the setup lock before following the live log.
Version 0.5.1 adds a joystick-triggered OCR-to-RGB beginner demo. Version 0.5.2
adds the established CodyJoy countdown/cue and USB-speaker shutter sound to every
bundled camera-capture example, with a CodyJoy buzzer fallback for shutter playback.
Version 0.5.3 replaces the complete system-owned examples folder on every setup run,
uses stable camera filenames, adds adjustable OCR sensitivity and tolerant text
matching, keeps OCR result LEDs on for five seconds, and adds `codynick-version`.

**Use this same command for first installation, a supported upgrade, or application
repair. Already on the verified hotspot? Run it now without rewriting the SD card:**

```bash
wget -O /tmp/codynick-setup.sh https://raw.githubusercontent.com/Sohaware/rpi/main/setup.sh && sudo bash /tmp/codynick-setup.sh
```

It chooses the required stage and shows the installation log. It accepts core
0.2.0, 0.2.1, 0.2.2, 0.3.0, the unpublished 0.3.1 candidate, 0.4.0, 0.5.0,
0.5.1, 0.5.2, and repeats of 0.5.3. Upstream stage scripts/assets are pinned
to immutable versions with SHA256 checks. Only the small entry point follows main;
the application and network stages use fixed release tags.

On a fresh OS, the network switch still disconnects SSH. Join the displayed Pi
hotspot, reconnect at 10.42.0.1, and run **the same command** within 15 minutes.
It performs the network confirmation and continues to applications. No separate
`--confirm` command is required with this entry point. Answer its confirmation prompt.

Have the USB webcam and a USB microphone (a webcam microphone is acceptable)
connected. Upgrading from 0.4.0 adds approximately **100 MB** of OCR downloads; a fresh
0.5.3 installation downloads approximately **456 MB**. Allow at least 3 GB free storage.
Downloads are cached and verified; repair restores managed runtime files.
Text-to-speech, face features, and chapter 8 are not installed yet. This remains a
staged hardware trial, not a production fleet updater.

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

## 3. Run the single setup command

```bash
wget -O /tmp/codynick-setup.sh https://raw.githubusercontent.com/Sohaware/rpi/main/setup.sh && sudo bash /tmp/codynick-setup.sh
```

The entry banner is **0.5.3**; its pinned network component still reports **0.1.2**.
On first installation, answer `y` to
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
wget -O /tmp/codynick-setup.sh https://raw.githubusercontent.com/Sohaware/rpi/main/setup.sh && sudo bash /tmp/codynick-setup.sh
```

Answer `y`. Success reports `Stage: network-ready` and disables rollback, then the
same entry point starts application installation. Wait for `CodyNick 0.5.3: READY`
before rebooting. No root password is set. The older internal network helper may
still mention `--confirm`; the unified entry point invokes it for you.

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

**Keep this SD card.** Use the unified command for application repair/upgrade.
The optional network-only `--check` command above checks just the network component.

## 6. Applications and USB-camera acceptance test

**Already connected to the verified hotspot? Start here. Do not rewrite the SD card
or repeat the network handover.** Keep the external internet network available.

Run these commands in the Pi's existing administrator SSH session at `10.42.0.1`:

```bash
wget -O /tmp/codynick-setup.sh https://raw.githubusercontent.com/Sohaware/rpi/main/setup.sh && sudo bash /tmp/codynick-setup.sh
```

Installation runs in the background, so closing SSH does not stop it. Do not reboot
or power off until it finishes. The command automatically follows its log.
Wait for **`CodyNick 0.5.3: READY`**, then press
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

**USB-camera/YOLO test:** In the IDE, open `CodyNick examples/camera_objects.py`
and click **Run this File**. The script finds USB video devices, plays the CodyJoy
get-ready cue and USB-speaker shutter sound, captures an image,
loads YOLO nano, and prints object detections. Point the webcam at ordinary objects
such as a chair, bottle, or cup. Zero detections is a valid result for an empty or
unrecognized scene, not proof of a broken installation.

The camera-open message should be green, without visible escape codes. Open the
IDE's **Images** section to inspect `usb_camera_test.jpg` and the annotated output
under `results`. The example closes its camera/worker when finished. Installation
itself does not capture photos: it validates the Python runtime and model warmup.
If capture fails, send the IDE terminal output; camera hardware confirmation remains
separate from the installer READY status. Close other programs using the webcam.

**USB-camera/OCR test:** In the IDE, open `CodyNick examples/camera_read_text.py`
and click **Run this File**. Hold a page or card with large printed English text in
good light. The script captures one photo, corrects a document-like perspective when
possible, reads the text offline with the standard model, and prints text-region and
average-confidence results. Inspect the original picture, annotated picture, and JSON
result in **Images/results**. It uses the same capture sounds as the object demo. No
photo or recognized text is sent to a cloud service.

### Installed scope and credentials

| Item | Details |
| --- | --- |
| Web applications | `/var/www/html`: Python IDE/live log, Blockly, dashboard, documentation |
| Python libraries and student code | `/home/client`; CodyNick.py 1.20.1 and Dashboard.py |
| Script watcher | `/root/codynick`, `codynick.service` |
| Student script execution | `script.service`, runs as `client`, unbuffered output to `/home/client/log.log` |
| Student Python runtime | `/home/client/.codynick-ai/envs/controller/bin/python` (bundled Python 3.10); keyboard, PySerial, requests, MySQL connector, NumPy/OpenCV |
| YOLO worker | `/home/client/.codynick-ai/envs/yolo/bin/python`; models in `/home/client/.deepface/weights`; AI source in `/home/client/vhl_object_detection` |
| OCR worker | `/home/client/.codynick-ai/envs/ocr/bin/python`; offline English fast/standard/best Tesseract models |
| SSH administrator | Existing username/password or key, unchanged |
| New client account | `client` / `codynick`; existing account passwords are not reset |
| Dashboard database | Database/user/password: `codynick` / `codynick` / `codynick`; database-scoped permissions |
| Root login/password | Unchanged; root login is not required |
| AI environments/models | USB-camera capture, YOLO nano/small/medium, offline English speech commands, and English OCR fast/standard/best |

This is a trusted-classroom-network application, not an internet-facing service.
The IDE does not provide user authentication or isolate students from one another.
Do not forward its web or SSH ports to the internet. Change default account passwords
before deployment outside a controlled classroom. Installing `keyboard` fixes its
import; Linux keyboard-hook operations may still require privileges and are not
validated by the import check.

### Repeating, checking, and recovering

**If 0.2.0 or 0.2.1 failed at the www-data write-access check, run the three commands above.**
No manual permission commands or SD-card rewrite are required. Version 0.5.3 accepts
failed and completed 0.2.0/0.2.1 installations and repairs web-user access with explicit
ACLs. It grants traversal of `/home` and `/home/client`, writes to the active script
and log, and shared-folder access. It does not grant writes to the whole client home.
On upgrades, the old `/opt/codynick/core-0.2.0` environment is retained, but the
student service now uses the bundled controller environment documented above.
Actual file opens are checked without truncating data, and disposable files test folder
create/read/rename/delete operations. No external `test -w` gates those checks.
Failures include identity, path, and ACL diagnostics. The 0.2.1 Pi log shows correct
ACLs/group membership but a failing `test -w`; its exact cause is still unconfirmed.

Repeat the same download/run commands to retry or repair **this core version**. It
rechecks dependencies and redeploys managed application files. It preserves saved
Python files outside `CodyNick examples`, active_script.py, media, logs, dashboard
records, web configuration, saved Blockly arrangements/packages, and existing account
passwords. The running student script is restarted during installation.

**`CodyNick examples` is a system-owned folder.** Every setup run backs up its old
contents, removes the complete live folder, and installs the current release set.
Do not save student work there because edits and extra files will disappear from the
live folder during installation, repair, or upgrade. The recovery copy is stored in
that run's `/var/backups/codynick/core-*` folder.

The application phase performs no OS-wide upgrade, reboot, root-password reset, or
network reconfiguration. A legacy installation or a version other than
0.2.0/0.2.1/0.2.2/0.3.0/0.3.1/0.4.0/0.5.0/0.5.1/0.5.2/0.5.3 is refused
rather than blindly overwritten. Other migrations are not yet implemented.
Edited managed source files are backed up before replacement;
this is not a full-system/database backup or transactional rollback. Back up important
student data separately before any deployment.

To view the installed component versions and run health checks:

```bash
sudo python3 /usr/local/lib/codynick/core-0.5.3/app_setup.py --check
```

For a compact version report and checksum status for every system example:

```bash
codynick-version
```

Each example is reported as `current`, `modified`, or `missing`; extra files are
reported as `unexpected`. Rerun the unified setup command to replace a changed
examples folder with the current set.

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

**Repair limits:** the single entry point requires a bootable OS, administrator
access, and working internet. It can start stopped existing network units, but it
does not reconstruct arbitrary missing/corrupt network state or unsupported legacy
installs. Runtime files are restored from the pinned snapshot; unknown conflicting
symlinks cause a safe failure. It is not a guarantee of recovery from every kind of
SD-card/OS damage. Keep an SD backup and do not downgrade by rerunning an old installer.

## Version history

| Version | Status | What is new |
| --- | --- | --- |
| **0.5.3-examples-polish** | Local validation passed; Pi hardware retest pending | Replaces the system-owned examples folder on every setup run; uses stable image names; adds adjustable OCR confidence, tolerant `codynick` matching, five-second LED results, and the `codynick-version` audit command. |
| **0.5.2-camera-sounds** | Local validation passed; Pi audio hardware test pending | All five bundled camera-capture examples play a CodyJoy countdown/cue and USB-speaker shutter sound, with a CodyJoy buzzer fallback. Existing AI assets and student data are preserved. |
| **0.5.1-ocr-led** | Local validation passed; Pi hardware test pending | Adds a one-shot joystick-UP camera OCR demo that turns all RGB LEDs green when normalized text contains `codynick`, otherwise red. Reuses 0.5.0 OCR assets. |
| **0.5.0-ocr** | Local validation passed; Pi OCR hardware test pending | Offline English fast/standard/best OCR, USB-camera text demo with confidence/JSON/annotation output, explicit PHP-first Apache homepage, interrupted-download retries, and setup-lock release before live log following. Application data and examples remain preserved. |
| **0.4.1-setup** | Clean-install retest pending | The second run recognizes the saved pending/applying network stage and opens confirmation without relying on SSH environment variables. Application payload remains 0.4.0. |
| **0.4.0-speech** | Voice LED hardware test passed on user's Pi | Offline English speech-to-text, constrained voice commands, microphone-to-RGB demo, and the camera/counting/model-comparison demos prepared in the unpublished 0.3.1 candidate. Reuses verified 0.3.0 vision assets. |
| 0.3.1-vision | Unpublished candidate, folded into 0.4.0 | Renamed camera demo, per-photo object counting, and sequential nano/small/medium comparison on one photo. |
| 0.3.0-vision | USB capture and default-model object detection passed on user's Pi | Single setup entry point, in-place upgrades from core 0.2.x, bundled ARM64 controller/YOLO runtime and models, USB-camera IDE example, safe ANSI terminal colors, bounded output, and log-rotation handling. OCR/speech/chapter 8 remain deferred. |
| 0.2.2-core | Fresh-OS, IDE/run/live-output, and RGB hardware tests passed on user's Pi | Replaced the failing external test -w gate with actual file/folder operations. Baseline for 0.3.0 upgrade. |
| 0.2.1-core | Superseded: test -w still failed on Pi | Added explicit ACLs and diagnostics. The log confirmed correct file modes, ACLs, and group membership, but the preliminary test prevented the real-open probe from running. |
| 0.2.0-core | Superseded: Pi health check failed on www-data write access | Introduced detached core installation, IDE/live terminal, Blockly, dashboard, dependencies, and script/watchdog services. Python/database checks passed on the Pi, but READY was not reached. |
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

1. Install 0.5.3 on the Pi and test clean example replacement, `codynick-version`,
   stable image replacement, OCR sensitivity/matching, five-second LEDs, camera
   sounds, repeated installation, and reboot persistence.
2. Package text-to-speech and face features later, retaining
   existing on-device paths and student data.
3. Add verified migrations and recovery for later releases, then test the complete
   clean-OS procedure before recommending fleet-wide upgrades.

Chapter 8 will be a separate upgrade. Keep this SD card for the next stage.

## AI demo gallery (0.5.3)

Open `CodyNick examples` in the IDE and select **Run This File**:

| Script | Demo |
| --- | --- |
| `camera_objects.py` | Capture one photo, print labels/scores, save an annotated image. |
| `object_counter.py` | Count `bottle` in five photos. Edit TARGET to another YOLO label. Counts are per-photo, not unique tracked objects across time. |
| `model_comparison.py` | Capture one photo, run nano/small/medium sequentially at the same threshold, and print load time and median of three detection calls. Each model saves its own annotated image. |
| `voice_led_colors.py` | Listen offline for English color commands and set all 16 RGB LEDs. Say lights off or stop listening to finish. |
| `camera_read_text.py` | Capture printed English text, run offline standard OCR, print confidence, and save annotated JPG plus JSON results. |
| `joystick_ocr_led.py` | Wait for CodyJoy Pro joystick UP, capture text, then fill all RGB LEDs green for `codynick` or red otherwise. |

Each demo uses one stable base name and overwrites its previous images/results instead
of accumulating random names. Model comparison keeps three stable annotated outputs,
one per model. Find annotations under Images/results. Every camera-capture demo uses
CodyJoy for its get-ready cue and a USB audio output for the shutter sound;
if USB playback is unavailable, CodyJoy plays a fallback shutter cue. These demos use
the USB webcam and existing models, with no cloud credentials or extra downloads.
Larger models may take longer and use more RAM. Comparison excludes an untimed
detection and image saving from timed calls. It measures full controller calls,
not pure inference; counts/scores are not accuracy measurements. Inspect the images.

The voice demo uses a constrained command list: red, green, blue, yellow, white,
purple, lights off, and stop listening. It automatically selects an ALSA USB/webcam
microphone, prints accepted commands and model confidence scores, and turns the LEDs
off when it exits. Recognition is offline; audio is streamed to the local worker and
is not saved or sent to a cloud service.

Set `OCR_CONFIDENCE` in either OCR example to adjust filtering: lower values accept
more uncertain text and higher values are stricter. In `joystick_ocr_led.py`,
`MATCH_SIMILARITY` controls tolerance for small OCR mistakes. The defaults are `0.20`
and `0.80`. Configurable uplink credentials, dongle replacement reconciliation, and
swap remain postponed; version 0.5.3 does not add them.

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
