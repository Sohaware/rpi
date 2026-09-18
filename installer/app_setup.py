#!/usr/bin/env python3
"""CodyNick core installer. Network configuration is owned by network_setup.py."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import urllib.request

VERSION = "0.2.0"
TAG = "v0.2.0-core"
BASE = f"https://raw.githubusercontent.com/Sohaware/rpi/{TAG}/"
STATE = Path("/var/lib/codynick/application-state.json")
NETWORK = Path("/var/lib/codynick/network-setup.json")
VENV = Path("/opt/codynick/core-0.2.0")
SERVICES = ("ssh", "codynick-ap", "codynick-dhcp", "codynick-nat")
PRESERVE = {"code/config.php", "dashboard/config.php", "docs/config.php", "blocks/data/main.json"}


def run(*args, **kwargs):
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], check=True, umask=0o022, **kwargs)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def safe_destination(path):
    path = Path(path)
    for part in (path, *path.parents):
        if part.is_symlink():
            raise RuntimeError(f"Refusing symlink destination: {part}")
    return path


def write(path, text, mode=0o644):
    path = safe_destination(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".codynick-new")
    safe_destination(tmp)
    tmp.write_text(text, encoding="utf-8")
    tmp.chmod(mode)
    tmp.replace(path)


def save_state(stage, **extra):
    data = read_json(STATE)
    data.update(version=VERSION, stage=stage, updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), **extra)
    write(STATE, json.dumps(data, indent=2) + "\n", 0o600)


def verify_manifest(manifest):
    if manifest.get("version") != VERSION or manifest.get("tag") != TAG:
        raise RuntimeError("Release manifest/version mismatch")
    files = manifest.get("files", {})
    if not files or len(files) > 300:
        raise RuntimeError("Invalid release file list")
    for name, sha in files.items():
        path = PurePosixPath(name)
        if len(path.parts) < 3 or path.is_absolute() or ".." in path.parts or "\\" in name or path.parts[0] != "components":
            raise RuntimeError(f"Invalid release path: {name}")
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise RuntimeError("Invalid release checksum")
        if path.parts[1] not in ("ide", "client", "watchdog"):
            raise RuntimeError("Unsupported component")
    return files


def download_sources(manifest, directory):
    for name, sha in verify_manifest(manifest).items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == sha:
            continue
        with urllib.request.urlopen(BASE + name, timeout=120) as response:
            data = response.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != sha:
            raise RuntimeError(f"Release checksum failed: {name}")
        target.write_bytes(data)


def deploy(source, destination, backup, preserve=False):
    destination = safe_destination(destination)
    if preserve and destination.exists():
        return
    if destination.exists():
        old = backup / str(destination).lstrip("/")
        old.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, old)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".codynick-new")
    safe_destination(temporary)
    shutil.copyfile(source, temporary)
    temporary.chmod(0o644)
    temporary.replace(destination)


def check_platform():
    info = platform.freedesktop_os_release()
    if info.get("ID") != "ubuntu" or info.get("VERSION_ID") != "26.04" or platform.machine() != "aarch64":
        raise RuntimeError("This trial requires Ubuntu 26.04 ARM64")
    if read_json(NETWORK).get("stage") != "network-ready":
        raise RuntimeError("Complete and confirm network setup first")
    for service in SERVICES:
        run("systemctl", "is-active", "--quiet", service)
    previous = read_json(STATE)
    if previous and previous.get("version") != VERSION:
        raise RuntimeError("This version cannot migrate that application release")
    if not previous and (Path("/root/codynick/service.py").exists() or Path("/home/client/CodyNick.py").exists()):
        raise RuntimeError("Existing legacy installation: migration must be reviewed before deployment")
    if shutil.disk_usage("/").free < 2 * 1024 ** 3:
        raise RuntimeError("At least 2 GiB free disk space is required")


def prepare_accounts():
    if subprocess.run(["id", "client"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        run("useradd", "--create-home", "--shell", "/bin/bash", "client")
        run("chpasswd", input="client:codynick\n", text=True)
    run("groupadd", "--force", "codynick-media")
    groups = ["codynick-media"]
    for group in ("dialout", "tty", "input", "video", "audio"):
        run("groupadd", "--force", group)
        groups.append(group)
    run("usermod", "-aG", ",".join(groups), "client")
    run("usermod", "-aG", "codynick-media", "www-data")
    for folder in ("userfiles", "images", "audio"):
        path = safe_destination(Path("/home/client") / folder)
        path.mkdir(parents=True, exist_ok=True)
        run("chown", "client:codynick-media", path)
        path.chmod(0o2775)
    home = safe_destination(Path("/home/client"))
    home.chmod(home.stat().st_mode | 0o005)
    for name, contents in (("active_script.py", "# Select a saved file in the IDE and click Run This File.\n"), ("log.log", "")):
        path = safe_destination(home / name)
        if not path.exists():
            write(path, contents, 0o664)
        run("chown", "client:codynick-media", path)
        path.chmod(0o664)
    write("/etc/udev/rules.d/70-codynick-access.rules", '\n'.join([
        'SUBSYSTEM=="tty", KERNEL=="ttyUSB*", GROUP="dialout", MODE="0660"',
        'SUBSYSTEM=="tty", KERNEL=="ttyACM*", GROUP="dialout", MODE="0660"',
        'SUBSYSTEM=="tty", KERNEL=="ttyAMA*", GROUP="dialout", MODE="0660"',
        'SUBSYSTEM=="input", KERNEL=="event*", GROUP="input", MODE="0660"', '']))
    run("udevadm", "control", "--reload-rules")
    run("udevadm", "trigger", "--subsystem-match=tty")
    run("udevadm", "trigger", "--subsystem-match=input")


def configure_database():
    run("systemctl", "enable", "--now", "mariadb")
    # IF NOT EXISTS deliberately leaves existing passwords and data untouched.
    sql = """CREATE DATABASE IF NOT EXISTS codynick CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'codynick'@'localhost' IDENTIFIED BY 'codynick';
GRANT ALL PRIVILEGES ON codynick.* TO 'codynick'@'localhost';
"""
    run("mariadb", input=sql, text=True)


def install_units():
    write("/etc/systemd/system/script.service", f"""[Unit]
Description=CodyNick student script
After=network.target mariadb.service
[Service]
Type=simple
User=client
Group=codynick-media
WorkingDirectory=/home/client
Environment=HOME=/home/client
Environment=PYTHONUNBUFFERED=1
Environment=PATH={VENV}/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={VENV}/bin/python -u /home/client/active_script.py
StandardOutput=append:/home/client/log.log
StandardError=append:/home/client/log.log
UMask=0002
Restart=no
KillMode=control-group
TimeoutStopSec=10
[Install]
WantedBy=multi-user.target
""")
    write("/etc/systemd/system/codynick.service", """[Unit]
Description=CodyNick script-change watchdog
After=network.target mariadb.service
[Service]
Type=simple
WorkingDirectory=/root/codynick
ExecStart=/usr/bin/python3 -u /root/codynick/service.py
Restart=on-failure
RestartSec=3
UMask=0002
[Install]
WantedBy=multi-user.target
""")
    write("/etc/apache2/conf-available/codynick.conf", """DirectoryIndex index.php index.html
<Directory /var/www/html>
    Options -Indexes
    AllowOverride None
    Require all granted
</Directory>
<IfModule mod_php.c>
    php_value upload_max_filesize 50M
    php_value post_max_size 55M
</IfModule>
""")
    write("/etc/systemd/system/apache2.service.d/codynick.conf", "[Service]\nProtectHome=false\nUMask=0002\n")
    run("a2enconf", "codynick")
    run("apache2ctl", "configtest")
    run("systemctl", "daemon-reload")
    run("systemctl", "enable", "apache2", "codynick", "script")
    run("systemctl", "restart", "apache2", "codynick", "script")


def health_check():
    for service in (*SERVICES, "apache2", "mariadb", "codynick"):
        run("systemctl", "is-active", "--quiet", service)
    run("runuser", "-u", "client", "--", VENV / "bin/python", "-c",
        "import sys;sys.path.insert(0,'/home/client');import keyboard,serial,requests,CodyNick,Dashboard;Dashboard.ensure_table();print('Python and database OK')")
    for name in ("active_script.py", "log.log", "userfiles", "images", "audio"):
        run("runuser", "-u", "www-data", "--", "test", "-w", f"/home/client/{name}")
    for url in ("/", "/code/", "/dashboard/", "/blocks/", "/docs/"):
        run("curl", "--fail", "--silent", "--show-error", "--max-time", "20", "--output", "/dev/null", "http://127.0.0.1" + url)


def install():
    check_platform()
    release = Path(__file__).resolve().parent
    manifest = read_json(release / "core-manifest.json")
    source = release / "payload"
    download_sources(manifest, source)
    backup = Path("/var/backups/codynick") / ("core-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    backup.mkdir(parents=True, mode=0o700)
    save_state("installing", backup=str(backup), components=manifest["components"])
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", NEEDRESTART_MODE="l")
    run("apt-get", "update", env=env)
    run("apt-get", "install", "-y", "apache2", "libapache2-mod-php", "php-mysql", "php-mbstring",
        "mariadb-server", "python3-venv", "python3-pip", "python3-requests", "python3-serial", "curl", "net-tools", env=env)
    run("python3", "-m", "venv", "--system-site-packages", VENV)
    run(VENV / "bin/python", "-m", "pip", "install", "--disable-pip-version-check", "keyboard==0.13.5", "mysql-connector-python==9.7.0")
    prepare_accounts()
    configure_database()
    for service in ("codynick", "script"):
        subprocess.run(["systemctl", "stop", service], check=False)
    for name in verify_manifest(manifest):
        relative = PurePosixPath(name)
        component = relative.parts[1]
        suffix = PurePosixPath(*relative.parts[2:])
        root = {"ide": Path("/var/www/html"), "client": Path("/home/client"), "watchdog": Path("/root/codynick")}[component]
        preserve = component == "ide" and (str(suffix) in PRESERVE or str(suffix).startswith("blocks/blocks/"))
        deploy(source / name, root / str(suffix), backup, preserve)
    for folder in (Path("/var/www/html/blocks/data"), Path("/var/www/html/blocks/blocks")):
        run("chown", "www-data:www-data", folder)
        folder.chmod(0o775)
        for item in folder.iterdir():
            if item.is_file() and not item.is_symlink():
                run("chown", "www-data:www-data", item)
    info = Path("/device_info.json")
    if not info.exists():
        write(info, json.dumps({"devicename": "CodyNick", "serial_number": read_json(NETWORK).get("ssid", "unknown"), "description": "CodyNick core 0.2.0 (AI installation pending)", "logo_path": "/assets/logo.png"}, indent=2))
    install_units()
    health_check()
    save_state("ready", completed_version=VERSION, ai_installed=False)
    print(f"\nCodyNick core {VERSION}: READY\nIDE: http://10.42.0.1/code/\nDashboard: http://10.42.0.1/dashboard/\nAI models/environments: NOT INSTALLED\nNo reboot required. Test Run This File and live output next.", flush=True)


def main():
    import fcntl
    os.umask(0o022)
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(f"CodyNick core installer {VERSION}", flush=True)
    if os.geteuid() != 0:
        raise SystemExit("Run with sudo")
    if args.check:
        state = read_json(STATE)
        print(json.dumps(state, indent=2))
        if state.get("stage") != "ready":
            raise SystemExit("Installation has not completed successfully; inspect the installation log")
        health_check()
        return
    if not args.worker:
        raise SystemExit("Use the download bootstrap to start installation")
    Path("/run/lock").mkdir(exist_ok=True)
    with open("/run/lock/codynick-app.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            install()
        except Exception as exc:
            if read_json(STATE).get("version") == VERSION:
                save_state("failed", error=str(exc))
            print(f"INSTALLATION FAILED: {exc}\nNetwork configuration was not changed. Keep the log for diagnosis.", file=sys.stderr, flush=True)
            raise


if __name__ == "__main__":
    main()
