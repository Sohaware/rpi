#!/usr/bin/env bash
set -euo pipefail
umask 022
VERSION="0.7.9"
VISION_SHA256="63e350ccdde8e755e194f97e2e3294ef2a90c10ca36d16fafaa78ce8c2edc1dc"
SPEECH_SHA256="c6a365e6ff8e5cde5a44e60fdffcaec7d0466349da41b42cbada937891fd4518"
OCR_SHA256="3524f9157a67f1196fff7a247ce2045452a58b9d9e86a70d271480eda06d2f0b"
TTS_SHA256="3ecd2d623c50fe3cc242904c9b3f5425b4245024430a791588f13ea5c37fff0c"
TAG="v0.7.9-voice-conversation"
HELPER_SHA256="63f79c571e321cc7344fe86a32f712040cf2961f75561598ba96c47a5198220f"
MANIFEST_SHA256="4025258cdf4c2b17198dd48e882cfb11f9c52f4ea3e5777acd0b78833b506681"
VERSION_STATUS_SHA256="71e8acac64fe20c70047bc1908d1de597d1f18aa4f8b39e93308fca277fa7814"
BASE="https://raw.githubusercontent.com/Sohaware/rpi/${TAG}"
echo "CodyNick core bootstrap ${VERSION} (offline voice conversation)"
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
wget --timeout=60 --tries=3 -O "$temp/core-manifest.json" "$BASE/releases/core-0.7.9.json"
wget --timeout=60 --tries=3 -O "$temp/version_status.py" "$BASE/installer/version_status.py"
wget --timeout=60 --tries=3 -O "$temp/vision_setup.py" "$BASE/installer/vision_setup.py"
wget --timeout=60 --tries=3 -O "$temp/speech_setup.py" "$BASE/installer/speech_setup.py"
wget --timeout=60 --tries=3 -O "$temp/ocr_setup.py" "$BASE/installer/ocr_setup.py"
wget --timeout=60 --tries=3 -O "$temp/tts_setup.py" "$BASE/installer/tts_setup.py"
printf '%s  %s\n' "$VISION_SHA256" "$temp/vision_setup.py" | sha256sum -c -
printf '%s  %s\n' "$SPEECH_SHA256" "$temp/speech_setup.py" | sha256sum -c -
printf '%s  %s\n' "$OCR_SHA256" "$temp/ocr_setup.py" | sha256sum -c -
printf '%s  %s\n' "$TTS_SHA256" "$temp/tts_setup.py" | sha256sum -c -
printf '%s  %s\n' "$HELPER_SHA256" "$temp/app_setup.py" "$MANIFEST_SHA256" "$temp/core-manifest.json" "$VERSION_STATUS_SHA256" "$temp/version_status.py" | sha256sum -c -
python3 - "$temp/core-manifest.json" <<'PY'
import json, pathlib, platform, sys
os_info = platform.freedesktop_os_release()
if os_info.get('ID') != 'ubuntu' or os_info.get('VERSION_ID') != '26.04' or platform.machine() != 'aarch64':
    raise SystemExit('Requires Ubuntu 26.04 ARM64')
state = pathlib.Path('/var/lib/codynick/network-setup.json')
if not state.exists() or json.loads(state.read_text()).get('stage') != 'network-ready':
    raise SystemExit('Complete and confirm network setup first')
if json.loads(pathlib.Path(sys.argv[1]).read_text()).get('version') != '0.7.9':
    raise SystemExit('Incorrect release manifest')
PY
install -d -m 0755 /usr/local/lib/codynick/core-0.7.9
install -m 0644 "$temp/app_setup.py" /usr/local/lib/codynick/core-0.7.9/app_setup.py
install -m 0644 "$temp/core-manifest.json" /usr/local/lib/codynick/core-0.7.9/core-manifest.json
install -m 0644 "$temp/version_status.py" /usr/local/lib/codynick/core-0.7.9/version_status.py
install -m 0644 "$temp/vision_setup.py" /usr/local/lib/codynick/core-0.7.9/vision_setup.py
install -m 0644 "$temp/speech_setup.py" /usr/local/lib/codynick/core-0.7.9/speech_setup.py
install -m 0644 "$temp/ocr_setup.py" /usr/local/lib/codynick/core-0.7.9/ocr_setup.py
install -m 0644 "$temp/tts_setup.py" /usr/local/lib/codynick/core-0.7.9/tts_setup.py
systemctl reset-failed codynick-install.service 2>/dev/null || true
# A transient unit survives SSH disconnection, but intentionally does not survive reboot.
flock -u 8
systemd-run --unit=codynick-install --collect --property=Type=exec \
    /usr/bin/python3 -u /usr/local/lib/codynick/core-0.7.9/app_setup.py --worker
echo
echo 'Installation is running in the background. Do not reboot until it finishes.'
echo 'Follow progress: sudo journalctl -fu codynick-install'
echo 'Success ends with: CodyNick 0.7.9: READY'
echo 'After success, open http://10.42.0.1/code/'
