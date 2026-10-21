"""Maintainer-only GitHub release selector. Pi users keep the same setup command."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = {
    '0.10.2': 'v0.10.2-tool-navigation',
    '0.10.1': 'v0.10.1-block-controls',
    '0.10.0': 'v0.10.0-gadget-simulator',
    '0.9.10': 'v0.9.10-temperature-nan',
    '0.9.9': 'v0.9.9-presenter-guide',
    '0.9.8': 'v0.9.8-temperature-time',
}


def render_selector(text, version, tag, digest):
    for name, value in [('TARGET_VERSION', version), ('TARGET_TAG', tag), ('TARGET_MANIFEST_SHA256', digest)]:
        text, count = re.subn(r'^' + name + r'="[^"]+"', name + '="' + value + '"', text, flags=re.MULTILINE)
        if count != 1:
            raise ValueError('Missing or ambiguous target selector: ' + name)
    return text


def published_manifest(version):
    tag = SUPPORTED[version]
    raw = subprocess.check_output(['git', 'show', f'{tag}:releases/core-{version}.json'], cwd=ROOT)
    manifest = json.loads(raw)
    if manifest.get('version') != version or manifest.get('tag') != tag:
        raise ValueError('Published tag does not match the selected release')
    return tag, hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version', choices=SUPPORTED)
    parser.add_argument('--check', action='store_true', help='show the selector without changing setup.sh')
    args = parser.parse_args()
    tag, digest = published_manifest(args.version)
    path = ROOT / 'setup.sh'
    updated = render_selector(path.read_text(), args.version, tag, digest)
    if not args.check:
        path.write_text(updated, encoding='utf-8', newline='\n')
    print(f'Selected original release {args.version} ({tag}); immutable manifest SHA256 {digest}')
    print('Updater engine and network pins are unchanged. Commit and push setup.sh to GitHub main.')
    print('The user then reruns the SAME fixed installation command. No custom Pi rollback command.')


if __name__ == '__main__':
    main()
