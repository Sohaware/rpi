#!/usr/bin/env bash
set -euo pipefail
umask 022
VERSION="0.5.0"
VISION_SHA256="63e350ccdde8e755e194f97e2e3294ef2a90c10ca36d16fafaa78ce8c2edc1dc"
SPEECH_SHA256="c6a365e6ff8e5cde5a44e60fdffcaec7d0466349da41b42cbada937891fd4518"
OCR_SHA256="3524f9157a67f1196fff7a247ce2045452a58b9d9e86a70d271480eda06d2f0b"
TAG="v0.5.0-ocr"
HELPER_SHA256="ceb610e9bdf6218c8e0588187971a89b4d630dc8f9093a8622a0d54d54cfcdd2"
MANIFEST_SHA256="a2d2789f0f2c565755de69af13e76e438bf3fb2036decd50398851b0b5141dd2"
BASE="https://raw.githubusercontent.com/Sohaware/rpi/${TAG}"
echo "CodyNick core bootstrap ${VERSION} (offline English OCR)"
if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo bash /tmp/codynick-apps.sh" >&2
    exit 1
fi
exec 9>/run/lock/codynick-app-bootstrap.lock
flock -n 9 || { echo "Another bootstrap is running." >&2; exit 1; }
if systemctl is-active --quiet codynick-install.service; then
    echo "Installation is already running. Follow it with: sudo journalctl -fu codynick-install"
    exit 0
fi
# Lock the worker separately so a failed unit cannot race a manually started worker.
exec 8>/run/lock/codynick-app.lock
flock -n 8 || { echo "An application installer is already running." >&2; exit 1; }
temp=$(mktemp -d)
trap 'rm -rf -- "$temp"' EXIT
wget --timeout=60 --tries=3 -O "$temp/app_setup.py" "$BASE/installer/app_setup.py"
wget --timeout=60 --tries=3 -O "$temp/core-manifest.json" "$BASE/releases/core-0.5.0.json"
wget --timeout=60 --tries=3 -O "$temp/vision_setup.py" "$BASE/installer/vision_setup.py"
wget --timeout=60 --tries=3 -O "$temp/speech_setup.py" "$BASE/installer/speech_setup.py"
wget --timeout=60 --tries=3 -O "$temp/ocr_setup.py" "$BASE/installer/ocr_setup.py"
printf '%s  %s\n' "$VISION_SHA256" "$temp/vision_setup.py" | sha256sum -c -
printf '%s  %s\n' "$SPEECH_SHA256" "$temp/speech_setup.py" | sha256sum -c -
printf '%s  %s\n' "$OCR_SHA256" "$temp/ocr_setup.py" | sha256sum -c -
printf '%s  %s\n' "$HELPER_SHA256" "$temp/app_setup.py" "$MANIFEST_SHA256" "$temp/core-manifest.json" | sha256sum -c -
python3 - "$temp/core-manifest.json" <<'PY'
import json, pathlib, platform, sys
os_info = platform.freedesktop_os_release()
if os_info.get('ID') != 'ubuntu' or os_info.get('VERSION_ID') != '26.04' or platform.machine() != 'aarch64':
    raise SystemExit('Requires Ubuntu 26.04 ARM64')
state = pathlib.Path('/var/lib/codynick/network-setup.json')
if not state.exists() or json.loads(state.read_text()).get('stage') != 'network-ready':
    raise SystemExit('Complete and confirm network setup first')
if json.loads(pathlib.Path(sys.argv[1]).read_text()).get('version') != '0.5.0':
    raise SystemExit('Incorrect release manifest')
PY
install -d -m 0755 /usr/local/lib/codynick/core-0.5.0
install -m 0644 "$temp/app_setup.py" /usr/local/lib/codynick/core-0.5.0/app_setup.py
install -m 0644 "$temp/core-manifest.json" /usr/local/lib/codynick/core-0.5.0/core-manifest.json
install -m 0644 "$temp/vision_setup.py" /usr/local/lib/codynick/core-0.5.0/vision_setup.py
install -m 0644 "$temp/speech_setup.py" /usr/local/lib/codynick/core-0.5.0/speech_setup.py
install -m 0644 "$temp/ocr_setup.py" /usr/local/lib/codynick/core-0.5.0/ocr_setup.py
systemctl reset-failed codynick-install.service 2>/dev/null || true
# A transient unit survives SSH disconnection, but intentionally does not survive reboot.
flock -u 8
systemd-run --unit=codynick-install --collect --property=Type=exec \
    /usr/bin/python3 -u /usr/local/lib/codynick/core-0.5.0/app_setup.py --worker
echo
echo 'Installation is running in the background. Do not reboot until it finishes.'
echo 'Follow progress: sudo journalctl -fu codynick-install'
echo 'Success ends with: CodyNick 0.5.0: READY'
echo 'After success, open http://10.42.0.1/code/'
