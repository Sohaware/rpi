#!/usr/bin/env bash
# Stable public entry point. Every published update pins immutable stage scripts.
set -euo pipefail
umask 022
VERSION="0.6.0"
NETWORK_SHA256="9f4d334da0561f97d51c7f6ee14eb6b123ec75d93d398bafb69ac35c2a6d82ae"
APPS_SHA256="ece279d1e605c05aa86c7ae4480999a5be31e86e5fcd7639e1e351cee44ec936"
[[ $EUID -eq 0 ]] || { echo 'Run this setup command using sudo.'; exit 1; }
echo "CodyNick setup ${VERSION}: install / repair / upgrade"
exec 7>/run/lock/codynick-setup-entry.lock
flock -n 7 || { echo 'Another setup command is running.'; exit 1; }
temp=$(mktemp -d)
trap 'rm -rf -- "$temp"' EXIT
fetch() {
    wget --timeout=60 --tries=3 -O "$temp/$1" "$2"
    printf '%s  %s\n' "$3" "$temp/$1" | sha256sum -c -
}
stage() {
    python3 - <<'PY'
import json,pathlib
p=pathlib.Path('/var/lib/codynick/network-setup.json')
print(json.loads(p.read_text()).get('stage','') if p.exists() else '')
PY
}
state=$(stage)
initial_state=$state
if [[ "$state" != network-ready ]]; then
    fetch network.sh https://raw.githubusercontent.com/Sohaware/rpi/v0.1.2-network/bootstrap/codynick-setup.sh "$NETWORK_SHA256"
    bash "$temp/network.sh"
    state=$(stage)
    if [[ "$state" == pending || "$state" == applying ]]; then
        if [[ "$initial_state" == pending || "$initial_state" == applying ]]; then
            /usr/local/sbin/codynick-setup --confirm
        else
            echo 'Join the displayed Pi hotspot and reconnect to SSH at 10.42.0.1.'
            echo 'Run this SAME setup command there within 15 minutes to confirm and continue.'
            exit 0
        fi
    fi
    [[ $(stage) == network-ready ]] || { echo 'Network stage is incomplete. Rerun this same setup command after resolving the reported problem.'; exit 1; }
fi
# Do not restart a working hotspot. Recover stopped existing units without rewriting settings.
for service in ssh codynick-ap codynick-dhcp codynick-nat; do
    if ! systemctl is-active --quiet "$service"; then
        systemctl start "$service" || { echo "Network service $service needs recovery; application installation was not started."; exit 1; }
    fi
done
fetch apps.sh https://raw.githubusercontent.com/Sohaware/rpi/v0.6.0-tts/bootstrap/codynick-apps.sh "$APPS_SHA256"
bash "$temp/apps.sh"
echo 'Progress follows. Ctrl+C closes this display only; background installation continues.'
flock -u 7
exec 7>&-
journalctl -fu codynick-install
