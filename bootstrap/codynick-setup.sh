#!/usr/bin/env bash
set -euo pipefail

VERSION="0.1.2"
REF="v0.1.2-network"
HELPER_SHA256="ccd2473739ab2edb61332cfe645ca04bd9ef17d5e3373db3c88169dd49f37f2b"
BASE_URL="https://raw.githubusercontent.com/Sohaware/rpi/$REF"

echo "CodyNick setup $VERSION - network trial (phase 1)"
if [[ ${1:-} == --version ]]; then exit 0; fi
if [[ $EUID -ne 0 ]]; then
    echo "Run this script with sudo from your existing administrator account." >&2
    exit 1
fi
case "${1:-}" in
    ""|--check|--confirm|--rollback) ;;
    *) echo "Usage: sudo bash codynick-setup.sh [--check|--confirm|--rollback]" >&2; exit 2 ;;
esac
if ! command -v python3 >/dev/null || ! command -v wget >/dev/null; then
    echo "Ubuntu must have python3 and wget installed." >&2
    exit 1
fi
if [[ -n ${1:-} && -f /usr/local/lib/codynick/network_setup.py ]]; then
    exec /usr/bin/python3 /usr/local/lib/codynick/network_setup.py "$@"
fi
umask 077
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
wget --https-only --timeout=30 --tries=3 -O "$tmp/network_setup.py" \
    "$BASE_URL/bootstrap/network_setup.py"
printf '%s  %s\n' "$HELPER_SHA256" "$tmp/network_setup.py" | sha256sum -c -
install -d -m 0755 /usr/local/lib/codynick
install -m 0644 "$tmp/network_setup.py" /usr/local/lib/codynick/network_setup.py
cat > "$tmp/codynick-setup" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/local/lib/codynick/network_setup.py "$@"
EOF
install -m 0755 "$tmp/codynick-setup" /usr/local/sbin/codynick-setup
umask 022
/usr/bin/python3 /usr/local/lib/codynick/network_setup.py "$@"
