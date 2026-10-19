#!/usr/bin/env bash
set -euo pipefail
umask 022
VERSION="0.9.6"
VISION_SHA256="63e350ccdde8e755e194f97e2e3294ef2a90c10ca36d16fafaa78ce8c2edc1dc"
SPEECH_SHA256="c6a365e6ff8e5cde5a44e60fdffcaec7d0466349da41b42cbada937891fd4518"
OCR_SHA256="3524f9157a67f1196fff7a247ce2045452a58b9d9e86a70d271480eda06d2f0b"
TTS_SHA256="3ecd2d623c50fe3cc242904c9b3f5425b4245024430a791588f13ea5c37fff0c"
LLM_SHA256="d22acd8c728ffd5b84d9bc9d7e76f4892648e6fa057e8fb78a238dab4602d2ed"
TAG="v0.9.6-dashboard-axes"
HELPER_SHA256="5cef0906ee351c5b662ea62e9d51930b407a7fc9604b2d195c9ae9f88a655e5d"
MANIFEST_SHA256="e97c5261a2f13405a39185f013bd1cb34793858b6afcaa6de7eda55fb980432e"
VERSION_STATUS_SHA256="fbd2604b00203bf7fc46d779a278a57a9c7a15a56116397e2a3ce868a5c33d56"
BASE="https://raw.githubusercontent.com/Sohaware/rpi/${TAG}"
echo "CodyNick core bootstrap ${VERSION} (local AI conversation and 5 GHz network)"
if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo bash /tmp/codynick-apps.sh" >&2
    exit 1
fi
exec 9>/run/lock/codynick-app-bootstrap.lock
flock -n 9 || { echo "Another bootstrap is running." >&2; exit 1; }
if systemctl is-active --quiet codynick-install.service; then
    echo "Installation is already running. Follow it with: codynick-install-log --follow"
    exit 0
fi
install -d -m 0755 /var/log/codynick
LOG=/var/log/codynick/install.log
if [[ -s "$LOG" ]]; then
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    mv "$LOG" "/var/log/codynick/install-${stamp}.log"
fi
touch "$LOG"
chmod 0644 "$LOG"
{ ls -1t /var/log/codynick/install-*.log 2>/dev/null || true; } | tail -n +6 | xargs -r rm --
cat > /usr/local/bin/codynick-install-status <<'EOF'
#!/usr/bin/env bash
set -u
if systemctl is-active --quiet codynick-install.service; then
    echo "Installer: running"
    systemctl show codynick-install.service --property=MainPID,ActiveEnterTimestamp --no-pager
else
    echo "Installer: not running"
fi
python3 - <<'PY'
import json
from pathlib import Path
p=Path('/var/lib/codynick/application-state.json')
if not p.exists():
    print('State: not created yet')
else:
    d=json.loads(p.read_text())
    for key in ('version','stage','operation','updated_at','completed_version','reboot_required','error'):
        if key in d: print(f'{key.replace("_"," ").title()}: {d[key]}')
PY
EOF
chmod 0755 /usr/local/bin/codynick-install-status
cat > /usr/local/bin/codynick-install-log <<'EOF'
#!/usr/bin/env bash
set -u
log=/var/log/codynick/install.log
if [[ ${1:-} == --follow ]]; then
    touch "$log"
    tail -n +1 -F "$log" & tail_pid=$!
    trap 'kill "$tail_pid" 2>/dev/null || true' EXIT INT TERM
    while systemctl is-active --quiet codynick-install.service; do sleep 2; done
    kill "$tail_pid" 2>/dev/null || true
    wait "$tail_pid" 2>/dev/null || true
    echo
    exec codynick-install-status
fi
exec cat "$log"
EOF
chmod 0755 /usr/local/bin/codynick-install-log
# Lock the worker separately so a failed unit cannot race a manually started worker.
exec 8>/run/lock/codynick-app.lock
flock -n 8 || { echo "An application installer is already running." >&2; exit 1; }
temp=$(mktemp -d)
trap 'rm -rf -- "$temp"' EXIT
wget -4 --timeout=60 --tries=3 -O "$temp/app_setup.py" "$BASE/installer/app_setup.py"
wget -4 --timeout=60 --tries=3 -O "$temp/core-manifest.json" "$BASE/releases/core-0.9.6.json"
wget -4 --timeout=60 --tries=3 -O "$temp/version_status.py" "$BASE/installer/version_status.py"
wget -4 --timeout=60 --tries=3 -O "$temp/vision_setup.py" "$BASE/installer/vision_setup.py"
wget -4 --timeout=60 --tries=3 -O "$temp/speech_setup.py" "$BASE/installer/speech_setup.py"
wget -4 --timeout=60 --tries=3 -O "$temp/ocr_setup.py" "$BASE/installer/ocr_setup.py"
wget -4 --timeout=60 --tries=3 -O "$temp/tts_setup.py" "$BASE/installer/tts_setup.py"
wget -4 --timeout=60 --tries=3 -O "$temp/llm_setup.py" "$BASE/installer/llm_setup.py"
printf '%s  %s\n' "$VISION_SHA256" "$temp/vision_setup.py" | sha256sum -c -
printf '%s  %s\n' "$SPEECH_SHA256" "$temp/speech_setup.py" | sha256sum -c -
printf '%s  %s\n' "$OCR_SHA256" "$temp/ocr_setup.py" | sha256sum -c -
printf '%s  %s\n' "$TTS_SHA256" "$temp/tts_setup.py" | sha256sum -c -
printf '%s  %s\n' "$LLM_SHA256" "$temp/llm_setup.py" | sha256sum -c -
printf '%s  %s\n' "$HELPER_SHA256" "$temp/app_setup.py" "$MANIFEST_SHA256" "$temp/core-manifest.json" "$VERSION_STATUS_SHA256" "$temp/version_status.py" | sha256sum -c -
python3 - "$temp/core-manifest.json" <<'PY'
import json, pathlib, platform, sys
os_info = platform.freedesktop_os_release()
if os_info.get('ID') != 'ubuntu' or os_info.get('VERSION_ID') != '26.04' or platform.machine() != 'aarch64':
    raise SystemExit('Requires Ubuntu 26.04 ARM64')
state = pathlib.Path('/var/lib/codynick/network-setup.json')
if not state.exists() or json.loads(state.read_text()).get('stage') != 'network-ready':
    raise SystemExit('Complete and confirm network setup first')
if json.loads(pathlib.Path(sys.argv[1]).read_text()).get('version') != '0.9.6':
    raise SystemExit('Incorrect release manifest')
PY
install -d -m 0755 /usr/local/lib/codynick/core-0.9.6
install -m 0644 "$temp/app_setup.py" /usr/local/lib/codynick/core-0.9.6/app_setup.py
install -m 0644 "$temp/core-manifest.json" /usr/local/lib/codynick/core-0.9.6/core-manifest.json
install -m 0644 "$temp/version_status.py" /usr/local/lib/codynick/core-0.9.6/version_status.py
install -m 0644 "$temp/vision_setup.py" /usr/local/lib/codynick/core-0.9.6/vision_setup.py
install -m 0644 "$temp/speech_setup.py" /usr/local/lib/codynick/core-0.9.6/speech_setup.py
install -m 0644 "$temp/ocr_setup.py" /usr/local/lib/codynick/core-0.9.6/ocr_setup.py
install -m 0644 "$temp/tts_setup.py" /usr/local/lib/codynick/core-0.9.6/tts_setup.py
install -m 0644 "$temp/llm_setup.py" /usr/local/lib/codynick/core-0.9.6/llm_setup.py
systemctl reset-failed codynick-install.service 2>/dev/null || true
# A transient unit survives SSH disconnection, but intentionally does not survive reboot.
flock -u 8
systemd-run --unit=codynick-install --collect --property=Type=exec \
    --property=StandardOutput=append:${LOG} --property=StandardError=append:${LOG} \
    /usr/bin/python3 -u /usr/local/lib/codynick/core-0.9.6/app_setup.py --worker
echo
echo 'Installation is running in the background. Do not reboot until it finishes.'
echo 'Follow progress: codynick-install-log --follow'
echo 'Check status: codynick-install-status'
echo 'Success ends with: CodyNick 0.9.6: READY'
echo 'After success, open http://10.42.0.1/code/'
