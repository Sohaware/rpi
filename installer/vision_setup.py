"""Version 0.3.0: allowlisted, checksummed USB-vision runtime deployment."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

ROOTS = (
    'home/client/.local/share/uv/python/cpython-3.10.20-linux-aarch64-gnu',
    'home/client/.local/share/uv/python/cpython-3.10-linux-aarch64-gnu',
    'home/client/.codynick-ai/envs/controller', 'home/client/.codynick-ai/envs/yolo',
    'home/client/.deepface/weights/yolov8n.onnx',
    'home/client/.deepface/weights/yolov8s.onnx',
    'home/client/.deepface/weights/yolov8m.onnx',
)


def allowed(name):
    return any(name == root or name.startswith(root + '/') for root in ROOTS)


def validate_member(member):
    name = member.name
    if name.startswith('/') or '\\' in name or '..' in PurePosixPath(name).parts or not allowed(name):
        raise ValueError('Unexpected archive path: ' + name)
    if not (member.isfile() or member.isdir() or member.issym()):
        raise ValueError('Unsupported archive member: ' + name)
    if member.issym():
        target = posixpath.normpath(member.linkname.lstrip('/') if member.linkname.startswith('/') else posixpath.join(posixpath.dirname(name), member.linkname))
        if not allowed(target):
            raise ValueError('Archive link escapes runtime roots: ' + name)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def no_symlink_parents(path):
    for parent in path.parents:
        if parent.is_symlink():
            raise ValueError('Refusing symlink parent: ' + str(parent))


def restore_archive(archive, root=Path('/')):
    # Preflight every member before performing any writes. Never extract through links.
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        names = set()
        links = set()
        for member in members:
            validate_member(member)
            if member.name in names:
                raise ValueError('Duplicate archive member')
            names.add(member.name)
            if member.issym():
                links.add(member.name)
        for member in members:
            if any(str(p) in links for p in PurePosixPath(member.name).parents):
                raise ValueError('Archive member beneath symlink')
            no_symlink_parents(root / member.name)
        for member in members:
            dest = root / member.name
            no_symlink_parents(dest)
            if member.isdir():
                if dest.is_symlink():
                    raise ValueError('Runtime directory is a symlink: ' + str(dest))
                dest.mkdir(parents=True, exist_ok=True)
                dest.chmod(0o755)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            if member.issym():
                if dest.is_symlink() and os.readlink(dest) == member.linkname:
                    continue
                if dest.exists() or dest.is_symlink():
                    raise ValueError('Conflicting runtime link: ' + str(dest))
                dest.symlink_to(member.linkname)
            else:
                if dest.is_symlink():
                    raise ValueError('Runtime file is a symlink: ' + str(dest))
                fd, temp = tempfile.mkstemp(prefix='.codynick-', dir=dest.parent)
                try:
                    with os.fdopen(fd, 'wb') as out, tar.extractfile(member) as source:
                        shutil.copyfileobj(source, out)
                    os.chmod(temp, 0o755 if member.mode & 0o111 else 0o644)
                    os.replace(temp, dest)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)


def install(manifest, run):
    cache = Path('/var/cache/codynick/vision-0.3.0')
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    assets = manifest['vision_assets']
    required = sum(item['expanded_size'] + item['size'] for item in assets) + 512 * 1024 ** 2
    if shutil.disk_usage('/').free < required:
        raise RuntimeError(f'Vision installation needs {required // 1024 ** 2} MiB free space')
    # Download and verify the entire runtime set before changing any runtime file.
    for item in assets:
        name = item['name']
        if PurePosixPath(name).name != name or not name.endswith('-0.3.0.tar.gz'):
            raise ValueError('Invalid vision asset name')
        target = cache / name
        if target.exists() and target.stat().st_size == item['size'] and sha(target) == item['sha256']:
            continue
        print('Downloading vision asset:', name, flush=True)
        temp = target.with_suffix('.part')
        with urllib.request.urlopen('https://github.com/Sohaware/rpi/releases/download/v0.3.0-vision/' + name, timeout=180) as source, temp.open('wb') as out:
            received = 0
            report_at = 16 * 1024 ** 2
            for block in iter(lambda: source.read(1024 * 1024), b''):
                received += len(block)
                if received > item['size']:
                    raise RuntimeError('Vision download exceeds manifest size: ' + name)
                out.write(block)
                if received >= report_at:
                    print(f'{name}: {received // 1024 ** 2}/{item["size"] // 1024 ** 2} MiB', flush=True)
                    report_at += 16 * 1024 ** 2
        if temp.stat().st_size != item['size'] or sha(temp) != item['sha256']:
            raise RuntimeError('Vision asset checksum mismatch: ' + name)
        temp.replace(target)
    for service in ('codynick', 'script'):
        subprocess.run(['systemctl', 'stop', service], check=False)
    for item in assets:
        print('Restoring verified vision asset:', item['name'], flush=True)
        restore_archive(cache / item['name'])
    site = Path('/home/client/.codynick-ai/envs/controller/lib/python3.10/site-packages/codynick-source.pth')
    no_symlink_parents(site)
    if site.is_symlink():
        raise ValueError('Unexpected source-path symlink')
    site.write_text('/home/client/vhl_object_detection\n', encoding='utf-8')
    site.chmod(0o644)


def health_check(run):
    python = '/home/client/.codynick-ai/envs/yolo/bin/python'
    run('runuser', '-u', 'client', '--', 'env', 'HOME=/home/client',
        'PYTHONPATH=/home/client/vhl_object_detection', python, '-c',
        "from codynick_ai.workers.yolo_engine import YoloObjectDetector; d=YoloObjectDetector('/home/client/.deepface/weights/yolov8n.onnx'); print('YOLO warmup OK:',d.warmup())")
    nodes = sorted(str(path) for path in Path('/dev').glob('video*'))
    print('Video device nodes: ' + (', '.join(nodes) or 'none; connect a USB camera before the camera test'), flush=True)
    print('Camera capture is not performed by installation; run the IDE camera example.', flush=True)
