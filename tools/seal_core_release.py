"""Regenerate the core manifest and bootstrap pins before publishing a NEW tag."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    relative = path.relative_to(ROOT).as_posix()
    object_id = subprocess.check_output(
        ["git", "hash-object", "-w", "--path", relative, path],
        cwd=ROOT, text=True,
    ).strip()
    data = subprocess.check_output(
        ["git", "cat-file", "blob", object_id], cwd=ROOT,
    )
    return hashlib.sha256(data).hexdigest()


def main():
    files = {}
    for component in ("ide", "client", "watchdog", "ai", "examples", "gadget-tests"):
        for path in sorted((ROOT / "components" / component).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = sha(path)
    data = {
        "version": "0.8.1", "tag": "v0.8.1-local-llm", "status": "hardware-trial",
        "components": {"ide": "0.8.1-local-llm", "CodyNick.py": "1.22.0", "Dashboard.py": "image-20260711", "watchdog": "0.2.0", "vision": "0.7.0-camera-cleanup", "examples": "0.8.1", "gadget-tests": "0.7.8", "speech": "0.4.0-image-baseline", "ocr": "0.5.0-image-baseline", "tts": "0.6.1-permissions", "llm": "gemma-3-1b-it-q4_k_m"},
        "ai_installed": True, "ai_scope": ["usb-camera", "yolo", "speech-to-text", "voice-commands", "ocr-en", "tts-en", "saved-audio-playback", "offline-voice-conversation", "local-llm"], "files": files,
        "vision_assets": json.loads((ROOT / "releases/vision-0.3.0.json").read_text())["assets"],
        "speech_assets": json.loads((ROOT / "releases/speech-0.4.0.json").read_text())["assets"],
        "ocr_assets": json.loads((ROOT / "releases/ocr-0.5.0.json").read_text())["assets"],
        "tts_assets": json.loads((ROOT / "releases/tts-0.6.0.json").read_text())["assets"],
        "llm_assets": [
            {
                "kind": "runtime",
                "name": "llama-b10689-bin-ubuntu-arm64.tar.gz",
                "url": "https://github.com/ggml-org/llama.cpp/releases/download/b10689/llama-b10689-bin-ubuntu-arm64.tar.gz",
                "size": 13128231,
                "sha256": "b70d5f153e089fbdf6ef79531a5fd462831f09b29745f11a5a86607af11c29d2",
            },
            {
                "kind": "model",
                "name": "gemma-3-1b-it-Q4_K_M.gguf",
                "url": "https://huggingface.co/ggml-org/gemma-3-1b-it-GGUF/resolve/f9c28bcd85737ffc5aef028638d3341d49869c27/gemma-3-1b-it-Q4_K_M.gguf",
                "size": 806058240,
                "sha256": "8ccc5cd1f1b3602548715ae25a66ed73fd5dc68a210412eea643eb20eb75a135",
            },
        ],
    }
    manifest = ROOT / "releases/core-0.8.1.json"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    bootstrap = ROOT / "bootstrap/codynick-apps.sh"
    text = bootstrap.read_text(encoding="utf-8")
    for key, path in (("HELPER", ROOT / "installer/app_setup.py"), ("MANIFEST", manifest), ("VERSION_STATUS", ROOT / "installer/version_status.py"), ("VISION", ROOT / "installer/vision_setup.py"), ("SPEECH", ROOT / "installer/speech_setup.py"), ("OCR", ROOT / "installer/ocr_setup.py"), ("TTS", ROOT / "installer/tts_setup.py"), ("LLM", ROOT / "installer/llm_setup.py")):
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
