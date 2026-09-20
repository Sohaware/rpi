"""Build the allowlisted English Tesseract payload from the approved Pi image."""
import argparse
import json
from pathlib import Path

try:
    from .build_app_release import digest, pack_image
    from .import_baseline import ExtImage
except ImportError:
    from build_app_release import digest, pack_image
    from import_baseline import ExtImage

VERSION = "0.5.0"
TAG = "v0.5.0-ocr"


def build(image_path, root, output):
    root = Path(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    image = ExtImage(image_path)
    site = "/home/client/.codynick-ai/envs/ocr/lib/python3.9/site-packages"
    packages = (
        "numpy", "numpy.libs", "numpy-1.24.3.dist-info",
        "cv2", "opencv_python_headless.libs", "opencv_python_headless-4.8.1.78.dist-info",
        "PIL", "pillow.libs", "pillow-11.3.0.dist-info",
        "pytesseract", "pytesseract-0.3.13.dist-info",
        "packaging", "packaging-26.2.dist-info",
    )
    plans = (
        (
            "ocr-environment",
            [
                "/home/client/.local/share/uv/python/cpython-3.9.25-linux-aarch64-gnu",
                "/home/client/.local/share/uv/python/cpython-3.9-linux-aarch64-gnu",
                "/home/client/.codynick-ai/envs/ocr/pyvenv.cfg",
                "/home/client/.codynick-ai/envs/ocr/bin/python",
                "/home/client/.codynick-ai/envs/ocr/bin/python3",
                "/home/client/.codynick-ai/envs/ocr/bin/python3.9",
                *[f"{site}/{name}" for name in packages],
            ],
            "runtime",
        ),
        (
            "ocr-english-models",
            ["/home/client/.codynick-ai/models/tesseract"],
            "models",
        ),
    )
    assets = []
    for name, paths, kind in plans:
        target = output / f"{name}-{VERSION}.tar.gz"
        expanded = pack_image(image, paths, target)
        assets.append({
            "name": target.name,
            "kind": kind,
            "size": target.stat().st_size,
            "sha256": digest(target),
            "expanded_size": expanded,
        })
        print(target.name, target.stat().st_size, flush=True)
    manifest = {
        "version": VERSION,
        "tag": TAG,
        "os": "ubuntu",
        "os_version": "26.04",
        "arch": "aarch64",
        "language": "en",
        "engines": ["tesseract"],
        "models": ["fast", "standard", "best"],
        "assets": assets,
    }
    text = json.dumps(manifest, indent=2) + "\n"
    (output / "release.json").write_text(text, encoding="utf-8")
    (root / "releases" / f"ocr-{VERSION}.json").write_text(text, encoding="utf-8")
    print("Total compressed bytes", sum(item["size"] for item in assets), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="dist/0.5.0")
    args = parser.parse_args()
    build(args.image, args.root, args.output)
