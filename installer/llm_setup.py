"""Checksummed Gemma 3 1B and llama.cpp deployment for CodyNick 0.8.1."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import time
import urllib.request


VERSION = "0.8.1"
RUNTIME_ROOT = Path("/opt/codynick/llama-b10689")
MODEL_ROOT = Path("/home/client/.codynick-ai/models/llm")
MODEL_PATH = MODEL_ROOT / "gemma-3-1b-it-Q4_K_M.gguf"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url, target, item, label, attempts=4):
    for attempt in range(1, attempts + 1):
        temporary = target.with_suffix(target.suffix + ".part")
        try:
            with urllib.request.urlopen(url, timeout=180) as source, temporary.open("wb") as output:
                received = 0
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    received += len(block)
                    if received > item["size"]:
                        raise RuntimeError(f"{label} download exceeds manifest size")
                    output.write(block)
            if temporary.stat().st_size != item["size"] or sha(temporary) != item["sha256"]:
                raise RuntimeError(f"{label} checksum mismatch")
            temporary.replace(target)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == attempts:
                raise
            print(f"{label} download interrupted; retrying ({attempt}/{attempts})...", flush=True)
            time.sleep(3 * attempt)


def restore_runtime(archive):
    destination = RUNTIME_ROOT.parent
    destination.mkdir(parents=True, exist_ok=True, mode=0o755)
    staging = Path(tempfile.mkdtemp(prefix=".llama-b10689-", dir=destination))
    try:
        with tarfile.open(archive) as bundle:
            members = bundle.getmembers()
            for member in members:
                path = PurePosixPath(member.name)
                if (
                    not path.parts
                    or path.parts[0] != "llama-b10689"
                    or path.is_absolute()
                    or ".." in path.parts
                    or not (member.isfile() or member.isdir() or member.issym())
                ):
                    raise RuntimeError("Unexpected llama.cpp archive member: " + member.name)
                if member.issym():
                    target = PurePosixPath(member.linkname)
                    if target.is_absolute() or ".." in target.parts:
                        raise RuntimeError("Unsafe llama.cpp archive link: " + member.name)
            bundle.extractall(staging, filter="data")
        restored = staging / "llama-b10689"
        if not (restored / "llama-server").is_file():
            raise RuntimeError("llama.cpp archive does not contain llama-server")
        if RUNTIME_ROOT.exists() or RUNTIME_ROOT.is_symlink():
            if RUNTIME_ROOT.is_symlink() or not RUNTIME_ROOT.is_dir():
                raise RuntimeError("Refusing conflicting llama.cpp runtime path")
            shutil.rmtree(RUNTIME_ROOT)
        restored.replace(RUNTIME_ROOT)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def install(manifest, run):
    assets = {item["kind"]: item for item in manifest["llm_assets"]}
    if set(assets) != {"runtime", "model"}:
        raise RuntimeError("LLM manifest must contain runtime and model assets")
    required = assets["model"]["size"] + 512 * 1024 ** 2
    if shutil.disk_usage("/").free < required:
        raise RuntimeError(f"LLM installation needs {required // 1024 ** 2} MiB free space")

    cache = Path("/var/cache/codynick/llm-0.8.1")
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    runtime = assets["runtime"]
    runtime_archive = cache / runtime["name"]
    if not (
        runtime_archive.exists()
        and runtime_archive.stat().st_size == runtime["size"]
        and sha(runtime_archive) == runtime["sha256"]
    ):
        download(runtime["url"], runtime_archive, runtime, "llama.cpp runtime")
    restore_runtime(runtime_archive)

    model = assets["model"]
    MODEL_ROOT.mkdir(parents=True, exist_ok=True, mode=0o755)
    if not (
        MODEL_PATH.exists()
        and MODEL_PATH.stat().st_size == model["size"]
        and sha(MODEL_PATH) == model["sha256"]
    ):
        download(model["url"], MODEL_PATH, model, "Gemma model")
    run("chown", "-R", "client:client", MODEL_ROOT)
    run("chmod", "0755", RUNTIME_ROOT / "llama-server", RUNTIME_ROOT / "llama-cli")


def health_check(run):
    if MODEL_PATH.stat().st_size != 806058240:
        raise RuntimeError("Gemma model size check failed")
    run(
        "runuser", "-u", "client", "--", "env",
        f"LD_LIBRARY_PATH={RUNTIME_ROOT}",
        RUNTIME_ROOT / "llama-server", "--version",
    )
