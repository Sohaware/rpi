"""Build the allowlisted English speech-command payload from the approved Pi image."""
import argparse
import json
from pathlib import Path

try:
    from .build_app_release import digest, pack_image
    from .import_baseline import ExtImage
except ImportError:
    from build_app_release import digest, pack_image
    from import_baseline import ExtImage

VERSION = "0.4.0"
TAG = "v0.4.0-speech"


def build(image_path, root, output):
    root = Path(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    image = ExtImage(image_path)
    assets = []
    plans = (
        ("stt-environment", ["/home/client/.codynick-ai/envs/stt"], "runtime"),
        (
            "stt-english-small-model",
            ["/home/client/.vosk/vosk-model-small-en-us-0.15"],
            "models",
        ),
    )
    for name, paths, kind in plans:
        target = output / f"{name}-{VERSION}.tar.gz"
        expanded = pack_image(image, paths, target)
        assets.append(
            {
                "name": target.name,
                "kind": kind,
                "size": target.stat().st_size,
                "sha256": digest(target),
                "expanded_size": expanded,
            }
        )
        print(target.name, target.stat().st_size, flush=True)
    manifest = {
        "version": VERSION,
        "tag": TAG,
        "os": "ubuntu",
        "os_version": "26.04",
        "arch": "aarch64",
        "language": "en",
        "model": "small",
        "assets": assets,
    }
    (output / "release.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (root / "releases" / f"speech-{VERSION}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print("Total compressed bytes", sum(item["size"] for item in assets), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="dist/0.4.0")
    args = parser.parse_args()
    build(args.image, args.root, args.output)
