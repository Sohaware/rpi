#!/usr/bin/env python3
"""Build CodyNick TTS release assets from a Raspberry Pi ext4 image."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tarfile
import tempfile


RUNTIME_ROOTS = (
    "home/client/.codynick-ai/envs/tts",
)
MODEL_ROOTS = (
    "home/client/.local/share/tts/tts_models--en--ljspeech--glow-tts",
    "home/client/.local/share/tts/vocoder_models--en--ljspeech--multiband-melgan",
)


def parse_listing(output, roots):
    records = []
    current = {}
    for line in output.splitlines() + [""]:
        if not line.strip():
            name = current.get("Path", "").replace("\\", "/")
            if any(name == root or name.startswith(root + "/") for root in roots):
                current["Path"] = name
                records.append(current)
            current = {}
        elif " = " in line:
            key, value = line.split(" = ", 1)
            current[key.strip()] = value
    return records


def list_records(seven_zip, image, roots):
    patterns = [f"-ir!{root.replace('/', chr(92))}\\*" for root in roots]
    completed = subprocess.run(
        [str(seven_zip), "l", "-slt", str(image), *patterns],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    records = parse_listing(completed.stdout, roots)
    if not records:
        raise RuntimeError("No matching files found in the image")
    return records, patterns


def unix_mode(value, folder=False):
    permissions = str(value or "")[1:10]
    if len(permissions) != 9:
        return 0o755 if folder else 0o644
    mode = 0
    for index, character in enumerate(permissions):
        if character in "rwxstST":
            mode |= 1 << (8 - index)
    return mode


def timestamp(value):
    try:
        return int(datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S").timestamp())
    except (TypeError, ValueError):
        return 0


def write_archive(archive, staging, records):
    expanded_size = 0
    with tarfile.open(archive, "w:gz", compresslevel=6, format=tarfile.PAX_FORMAT) as bundle:
        for record in sorted(records, key=lambda item: item["Path"]):
            name = record["Path"]
            source = staging / Path(*PurePosixPath(name).parts)
            link = record.get("Symbolic Link")
            folder = record.get("Folder") == "+"
            info = tarfile.TarInfo(name)
            info.uid = int(record.get("User ID", 0))
            info.gid = int(record.get("Group ID", 0))
            info.mtime = timestamp(record.get("Modified"))
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = link
                info.mode = 0o777
                bundle.addfile(info)
            elif folder:
                info.type = tarfile.DIRTYPE
                info.mode = unix_mode(record.get("Mode"), folder=True)
                bundle.addfile(info)
            else:
                info.type = tarfile.REGTYPE
                info.size = int(record.get("Size", 0))
                info.mode = unix_mode(record.get("Mode"))
                expanded_size += info.size
                with source.open("rb") as stream:
                    bundle.addfile(info, stream)
    return expanded_size


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_regular_files(seven_zip, image, staging, records):
    regular = [
        record for record in records
        if record.get("Folder") != "+" and not record.get("Symbolic Link")
    ]
    list_file = staging.parent / f"{staging.name}-files.txt"
    list_file.write_text(
        "\n".join(record["Path"].replace("/", "\\") for record in regular) + "\n",
        encoding="utf-8",
    )
    try:
        completed = subprocess.run(
            [
                str(seven_zip), "x", "-y", "-scsUTF-8", f"-o{staging}",
                str(image), f"@{list_file}",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    finally:
        list_file.unlink(missing_ok=True)
    missing = [
        record["Path"] for record in regular
        if not (staging / Path(*PurePosixPath(record["Path"]).parts)).is_file()
    ]
    if missing:
        detail = (completed.stderr or "").strip().splitlines()[-5:]
        raise RuntimeError(
            "Image extraction missed files: " + ", ".join(missing[:5])
            + ("\n" + "\n".join(detail) if detail else "")
        )


def build_asset(seven_zip, image, output, staging_root, name, roots):
    records, _patterns = list_records(seven_zip, image, roots)
    with tempfile.TemporaryDirectory(prefix="ct", dir=staging_root) as temp:
        staging = Path(temp)
        extract_regular_files(seven_zip, image, staging, records)
        archive = output / name
        expanded = write_archive(archive, staging, records)
    return {
        "name": name,
        "size": archive.stat().st_size,
        "sha256": sha256(archive),
        "expanded_size": expanded,
        "entries": len(records),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seven-zip", type=Path,
                        default=Path(r"C:\Program Files\7-Zip\7z.exe"))
    parser.add_argument(
        "--staging-root",
        type=Path,
        default=Path(r"D:\ct"),
        help="Short temporary path used to avoid Windows path-length limits",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.staging_root.mkdir(parents=True, exist_ok=True)
    assets = [
        build_asset(args.seven_zip, args.image, args.output, args.staging_root,
                    "tts-environment-0.6.0.tar.gz", RUNTIME_ROOTS),
        build_asset(args.seven_zip, args.image, args.output, args.staging_root,
                    "tts-english-fast-model-0.6.0.tar.gz", MODEL_ROOTS),
    ]
    (args.output / "tts-assets.json").write_text(
        json.dumps(assets, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(assets, indent=2))


if __name__ == "__main__":
    main()
