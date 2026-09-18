#!/usr/bin/env python3

import hashlib
import os
import subprocess
import time
from pathlib import Path
from security import block_python_file_if_intrusion_detected

__version__ = "0.2.0"

# =========================
# Hardcoded configuration
# =========================

SERVICE_NAME = "script.service"
PYTHON_FILE_NAME = "/home/client/active_script.py"
LOG_OUTPUT_FILE_NAME = "/home/client/log.log"
HASH_FILE_NAME = "hash.txt"

CYCLE_SECONDS = 1


# =========================
# Paths
# =========================

WORKING_DIR = Path(__file__).resolve().parent

PYTHON_FILE_PATH = WORKING_DIR / PYTHON_FILE_NAME
LOG_OUTPUT_PATH = WORKING_DIR / LOG_OUTPUT_FILE_NAME
HASH_FILE_PATH = WORKING_DIR / HASH_FILE_NAME


# =========================
# Helper functions
# =========================

def calculate_sha256(file_path: Path) -> str:
    import fcntl
    sha256 = hashlib.sha256()

    with file_path.open("rb") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def read_previous_hash() -> str | None:
    if not HASH_FILE_PATH.exists():
        return None

    return HASH_FILE_PATH.read_text().strip()


def write_current_hash(file_hash: str) -> None:
    HASH_FILE_PATH.write_text(file_hash + "\n")


def write_log_output(content: str) -> None:
    try:
        LOG_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_OUTPUT_PATH.open("a", encoding="utf-8", buffering=1) as f:
            f.write(content)
        os.chmod(LOG_OUTPUT_PATH, 0o664)
    except Exception:
        pass


def restart_service() -> None:
    subprocess.run(
        ["systemctl", "restart", SERVICE_NAME],
        check=True
    )


# =========================
# Main loop
# =========================

def main() -> None:
    print(f"CodyNick watchdog {__version__} started.")

    while True:
        try:
            # 0. Run security task
            if (not block_python_file_if_intrusion_detected(PYTHON_FILE_NAME)):
                write_log_output("INTRUSION ATTEMPT DETECTED & BLOCKED\n")
            # 1. Check Python file hash
            if PYTHON_FILE_PATH.exists():
                current_hash = calculate_sha256(PYTHON_FILE_PATH)
                previous_hash = read_previous_hash()

                # Restart only if hash changed after the first recorded hash
                if previous_hash is not None and current_hash != previous_hash:
                    print("Python file changed. Restarting service...")
                    write_log_output("[watchdog] Python file changed. Restarting active script.\n")
                    restart_service()

                # A failed restart must be retried, not recorded as successful.
                write_current_hash(current_hash)

            else:
                write_log_output(
                    f"Python file not found: {PYTHON_FILE_PATH}\n"
                )

        except Exception as e:
            try:
                write_log_output(f"Watchdog error: {e}\n")
            except Exception:
                pass

        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    main()
