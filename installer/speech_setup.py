"""Version 0.4.0: allowlisted, checksummed offline speech deployment."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

VERSION = "0.4.0"
TAG = "v0.4.0-speech"
ROOTS = (
    "home/client/.codynick-ai/envs/stt",
    "home/client/.vosk/vosk-model-small-en-us-0.15",
)
LINK_ROOTS = ROOTS + (
    "home/client/.local/share/uv/python/cpython-3.10.20-linux-aarch64-gnu",
    "home/client/.local/share/uv/python/cpython-3.10-linux-aarch64-gnu",
)


def allowed(name):
    return any(name == root or name.startswith(root + "/") for root in ROOTS)


def allowed_link(name):
    return any(name == root or name.startswith(root + "/") for root in LINK_ROOTS)


def validate_member(member):
    name = member.name
    if name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts or not allowed(name):
        raise ValueError("Unexpected speech archive path: " + name)
    if not (member.isfile() or member.isdir() or member.issym()):
        raise ValueError("Unsupported speech archive member: " + name)
    if member.issym():
        target = posixpath.normpath(
            member.linkname.lstrip("/")
            if member.linkname.startswith("/")
            else posixpath.join(posixpath.dirname(name), member.linkname)
        )
        if not allowed_link(target):
            raise ValueError("Speech archive link escapes runtime roots: " + name)


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
                raise ValueError("Duplicate speech archive member")
            names.add(member.name)
            if member.issym():
                links.add(member.name)
        for member in members:
            if any(str(parent) in links for parent in PurePosixPath(member.name).parents):
                raise ValueError("Speech archive member beneath symlink")
            no_symlink_parents(root / member.name)
        for member in members:
            destination = root / member.name
            no_symlink_parents(destination)
            if member.isdir():
                if destination.is_symlink():
                    raise ValueError("Speech runtime directory is a symlink")
                destination.mkdir(parents=True, exist_ok=True)
                destination.chmod(0o755)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if member.issym():
                if destination.is_symlink() and os.readlink(destination) == member.linkname:
                    continue
                if destination.exists() or destination.is_symlink():
                    raise ValueError("Conflicting speech runtime link: " + str(destination))
                destination.symlink_to(member.linkname)
                continue
            if destination.is_symlink():
                raise ValueError("Speech runtime file is a symlink: " + str(destination))
            descriptor, temporary = tempfile.mkstemp(prefix=".codynick-", dir=destination.parent)
            try:
                with os.fdopen(descriptor, "wb") as output, bundle.extractfile(member) as source:
                    shutil.copyfileobj(source, output)
                os.chmod(temporary, 0o755 if member.mode & 0o111 else 0o644)
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)


def install(manifest, run):
    cache = Path("/var/cache/codynick/speech-0.4.0")
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    assets = manifest["speech_assets"]
    required = sum(item["expanded_size"] + item["size"] for item in assets) + 256 * 1024 ** 2
    if shutil.disk_usage("/").free < required:
        raise RuntimeError(f"Speech installation needs {required // 1024 ** 2} MiB free space")
    for item in assets:
        name = item["name"]
        if PurePosixPath(name).name != name or not name.endswith("-0.4.0.tar.gz"):
            raise ValueError("Invalid speech asset name")
        target = cache / name
        if target.exists() and target.stat().st_size == item["size"] and sha(target) == item["sha256"]:
            continue
        print("Downloading speech asset:", name, flush=True)
        temporary = target.with_suffix(".part")
        with urllib.request.urlopen(
            f"https://github.com/Sohaware/rpi/releases/download/{TAG}/{name}",
            timeout=180,
        ) as source, temporary.open("wb") as output:
            received = 0
            for block in iter(lambda: source.read(1024 * 1024), b""):
                received += len(block)
                if received > item["size"]:
                    raise RuntimeError("Speech download exceeds manifest size: " + name)
                output.write(block)
        if temporary.stat().st_size != item["size"] or sha(temporary) != item["sha256"]:
            raise RuntimeError("Speech asset checksum mismatch: " + name)
        temporary.replace(target)
    for item in assets:
        print("Restoring verified speech asset:", item["name"], flush=True)
        restore_archive(cache / item["name"])


def health_check(run):
    python = "/home/client/.codynick-ai/envs/stt/bin/python"
    run(
        "runuser", "-u", "client", "--", "env", "HOME=/home/client",
        "PYTHONPATH=/home/client/vhl_object_detection", python, "-c",
        "from codynick_ai.workers.vosk_engine import VoskSpeechRecognizer;"
        "r=VoskSpeechRecognizer('/home/client/.vosk/vosk-model-small-en-us-0.15',"
        "language='en',model_name='small');print('Offline English speech model OK')",
    )
    result = subprocess.run(["arecord", "-l"], text=True, capture_output=True)
    listing = (result.stdout or "") + (result.stderr or "")
    print("ALSA capture devices:\n" + (listing.strip() or "none; connect a USB microphone for the demo"), flush=True)
