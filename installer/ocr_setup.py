"""Version 0.5.0: allowlisted, checksummed English OCR deployment."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import tarfile
import tempfile
import time
import urllib.request

VERSION = "0.5.0"
TAG = "v0.5.0-ocr"
ROOTS = (
    "home/client/.codynick-ai/envs/ocr",
    "home/client/.codynick-ai/models/tesseract",
    "home/client/.local/share/uv/python/cpython-3.9.25-linux-aarch64-gnu",
    "home/client/.local/share/uv/python/cpython-3.9-linux-aarch64-gnu",
)


def allowed(name):
    return any(name == root or name.startswith(root + "/") for root in ROOTS)


def validate_member(member):
    name = member.name
    if name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts or not allowed(name):
        raise ValueError("Unexpected OCR archive path: " + name)
    if not (member.isfile() or member.isdir() or member.issym()):
        raise ValueError("Unsupported OCR archive member: " + name)
    if member.issym():
        target = posixpath.normpath(
            member.linkname.lstrip("/") if member.linkname.startswith("/")
            else posixpath.join(posixpath.dirname(name), member.linkname)
        )
        if not allowed(target):
            raise ValueError("OCR archive link escapes runtime roots: " + name)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def no_symlink_parents(path):
    for parent in path.parents:
        if parent.is_symlink():
            raise ValueError("Refusing symlink parent: " + str(parent))


def restore_archive(archive, root=Path("/")):
    with tarfile.open(archive) as bundle:
        members = bundle.getmembers()
        names = set()
        links = set()
        for member in members:
            validate_member(member)
            if member.name in names:
                raise ValueError("Duplicate OCR archive member")
            names.add(member.name)
            if member.issym():
                links.add(member.name)
        for member in members:
            if any(str(parent) in links for parent in PurePosixPath(member.name).parents):
                raise ValueError("OCR archive member beneath symlink")
            no_symlink_parents(root / member.name)
        for member in members:
            destination = root / member.name
            no_symlink_parents(destination)
            if member.isdir():
                if destination.is_symlink():
                    raise ValueError("OCR runtime directory is a symlink")
                destination.mkdir(parents=True, exist_ok=True)
                destination.chmod(0o755)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if member.issym():
                if destination.is_symlink() and os.readlink(destination) == member.linkname:
                    continue
                if destination.exists() or destination.is_symlink():
                    raise ValueError("Conflicting OCR runtime link: " + str(destination))
                destination.symlink_to(member.linkname)
                continue
            if destination.is_symlink():
                raise ValueError("OCR runtime file is a symlink: " + str(destination))
            descriptor, temporary = tempfile.mkstemp(prefix=".codynick-", dir=destination.parent)
            try:
                with os.fdopen(descriptor, "wb") as output, bundle.extractfile(member) as source:
                    shutil.copyfileobj(source, output)
                os.chmod(temporary, 0o755 if member.mode & 0o111 else 0o644)
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)


def download(url, target, item, attempts=4):
    for attempt in range(1, attempts + 1):
        temporary = target.with_suffix(".part")
        try:
            with urllib.request.urlopen(url, timeout=180) as source, temporary.open("wb") as output:
                received = 0
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    received += len(block)
                    if received > item["size"]:
                        raise RuntimeError("OCR download exceeds manifest size: " + item["name"])
                    output.write(block)
            if temporary.stat().st_size != item["size"] or sha(temporary) != item["sha256"]:
                raise RuntimeError("OCR asset checksum mismatch: " + item["name"])
            temporary.replace(target)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == attempts:
                raise
            print(f"OCR download interrupted; retrying ({attempt}/{attempts})...", flush=True)
            time.sleep(3 * attempt)


def install(manifest, run):
    cache = Path("/var/cache/codynick/ocr-0.5.0")
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    assets = manifest["ocr_assets"]
    required = sum(item["expanded_size"] + item["size"] for item in assets) + 256 * 1024 ** 2
    if shutil.disk_usage("/").free < required:
        raise RuntimeError(f"OCR installation needs {required // 1024 ** 2} MiB free space")
    for item in assets:
        name = item["name"]
        if PurePosixPath(name).name != name or not name.endswith("-0.5.0.tar.gz"):
            raise ValueError("Invalid OCR asset name")
        target = cache / name
        if target.exists() and target.stat().st_size == item["size"] and sha(target) == item["sha256"]:
            continue
        print("Downloading OCR asset:", name, flush=True)
        download(f"https://github.com/Sohaware/rpi/releases/download/{TAG}/{name}", target, item)
    for item in assets:
        print("Restoring verified OCR asset:", item["name"], flush=True)
        restore_archive(cache / item["name"])


def health_check(run):
    python = "/home/client/.codynick-ai/envs/ocr/bin/python"
    run(
        "runuser", "-u", "client", "--", "env", "HOME=/home/client",
        "PYTHONPATH=/home/client/vhl_object_detection", python, "-c",
        "from codynick_ai.workers.tesseract_engine import TesseractOcrEngine as E;"
        "E(['en'],model_name='fast');"
        "E(['en'],model_name='standard',tessdata_directory='/home/client/.codynick-ai/models/tesseract/standard');"
        "E(['en'],model_name='best',tessdata_directory='/home/client/.codynick-ai/models/tesseract/best');"
        "print('English OCR fast/standard/best models OK')",
    )
