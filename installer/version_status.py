#!/usr/bin/env python3
"""Show the installed CodyNick release and verify its system-owned examples."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


VERSION = "0.5.3"
STATE = Path("/var/lib/codynick/application-state.json")
EXAMPLES = Path("/home/client/userfiles/CodyNick examples")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def example_statuses(manifest):
    statuses = []
    expected_names = set()
    for name, expected in sorted(manifest.get("files", {}).items()):
        relative = PurePosixPath(name)
        if relative.parts[:2] != ("components", "examples"):
            continue
        suffix = PurePosixPath(*relative.parts[2:])
        expected_names.add(str(suffix))
        path = EXAMPLES / str(suffix)
        if not path.is_file():
            status = "missing"
        elif hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            status = "current"
        else:
            status = "modified"
        statuses.append({"name": str(suffix), "status": status})
    if EXAMPLES.is_dir():
        for path in sorted(EXAMPLES.rglob("*")):
            if path.is_file():
                name = path.relative_to(EXAMPLES).as_posix()
                if name not in expected_names:
                    statuses.append({"name": name, "status": "unexpected"})
    return statuses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    state = read_json(STATE)
    manifest = read_json(Path(__file__).resolve().with_name("core-manifest.json"))
    result = {
        "installed_version": state.get("version", "unknown"),
        "completed_version": state.get("completed_version"),
        "stage": state.get("stage", "unknown"),
        "components": state.get("components", {}),
        "examples": example_statuses(manifest),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"CodyNick installation: {result['installed_version']}")
        print(f"Stage: {result['stage']}")
        print("Components:")
        for name, version in sorted(result["components"].items()):
            print(f"  {name}: {version}")
        print("CodyNick examples:")
        for item in result["examples"]:
            print(f"  [{item['status']}] {item['name']}")
    healthy = (
        result["installed_version"] == VERSION
        and result["completed_version"] == VERSION
        and result["stage"] == "ready"
        and result["examples"]
        and all(item["status"] == "current" for item in result["examples"])
    )
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.exit(main())
