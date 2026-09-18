"""Regenerate the core manifest and bootstrap pins before publishing a NEW tag."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = {}
    for component in ("ide", "client", "watchdog"):
        for path in sorted((ROOT / "components" / component).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = sha(path)
    data = {
        "version": "0.2.1", "tag": "v0.2.1-core", "status": "hardware-trial",
        "components": {"ide": "Rev.B2-core.0.2.0", "CodyNick.py": "1.20.1", "Dashboard.py": "image-20260711", "watchdog": "0.2.0"},
        "ai_installed": False, "files": files,
    }
    manifest = ROOT / "releases/core-0.2.1.json"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    bootstrap = ROOT / "bootstrap/codynick-apps.sh"
    text = bootstrap.read_text(encoding="utf-8")
    for key, path in (("HELPER", ROOT / "installer/app_setup.py"), ("MANIFEST", manifest)):
        text = re.sub(key + r'_SHA256="[^"]+"', key + '_SHA256="' + sha(path) + '"', text)
    bootstrap.write_text(text, encoding="utf-8", newline="\n")
    print(f"Sealed {len(files)} core files; do not modify a published tag.")


if __name__ == "__main__":
    main()
