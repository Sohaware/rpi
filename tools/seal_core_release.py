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
    for component in ("ide", "client", "watchdog", "ai", "examples"):
        for path in sorted((ROOT / "components" / component).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = sha(path)
    data = {
        "version": "0.4.0", "tag": "v0.4.0-speech", "status": "hardware-trial",
        "components": {"ide": "0.3.0", "CodyNick.py": "1.20.1", "Dashboard.py": "image-20260711", "watchdog": "0.2.0", "vision": "0.3.0-image-baseline", "examples": "0.4.0", "speech": "0.4.0-image-baseline"},
        "ai_installed": True, "ai_scope": ["usb-camera", "yolo", "speech-to-text", "voice-commands"], "files": files,
        "vision_assets": json.loads((ROOT / "releases/vision-0.3.0.json").read_text())["assets"],
        "speech_assets": json.loads((ROOT / "releases/speech-0.4.0.json").read_text())["assets"],
    }
    manifest = ROOT / "releases/core-0.4.0.json"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    bootstrap = ROOT / "bootstrap/codynick-apps.sh"
    text = bootstrap.read_text(encoding="utf-8")
    for key, path in (("HELPER", ROOT / "installer/app_setup.py"), ("MANIFEST", manifest), ("VISION", ROOT / "installer/vision_setup.py"), ("SPEECH", ROOT / "installer/speech_setup.py")):
        text = re.sub(key + r'_SHA256="[^"]+"', key + '_SHA256="' + sha(path) + '"', text)
    bootstrap.write_text(text, encoding="utf-8", newline="\n")
    entry = ROOT / "setup.sh"
    text = entry.read_text()
    for key, path in (("NETWORK", ROOT / "bootstrap/codynick-setup.sh"), ("APPS", bootstrap)):
        text = re.sub(key + r'_SHA256="[^"]+"', key + '_SHA256="' + sha(path) + '"', text)
    entry.write_text(text, encoding="utf-8", newline="\n")
    print(f"Sealed {len(files)} core files; do not modify a published tag.")


if __name__ == "__main__":
    main()
