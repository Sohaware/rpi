"""Verify stage and named designs through the installed Apache context."""
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


def request(action, data=None):
    url = 'http://127.0.0.1/blocks/designs.php?action=' + action
    req = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise RuntimeError(str(result))
    return result


def main():
    for attempt in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1/blocks/stage.php', timeout=3) as response:
                result = json.load(response)
            if not result.get('ok'):
                raise RuntimeError(str(result))
            break
        except (OSError, ValueError, RuntimeError):
            if attempt == 29:
                raise
            time.sleep(.5)
    name = '__install_test_' + uuid.uuid4().hex
    existing = request('list')['designs']
    if len(existing) >= 500:
        request('load&name=' + urllib.parse.quote(existing[0]['name']))
        print('Sprite stage and design read checks passed; store is full, write test skipped.')
        return
    created = False
    try:
        workspace = {'blocks': {'languageVersion': 0, 'blocks': []}}
        request('save', {'name': name, 'workspace': workspace})
        created = True
        if request('load&name=' + name)['workspace'] != workspace:
            raise RuntimeError('Design load mismatch')
        if not any(item['name'] == name for item in request('list')['designs']):
            raise RuntimeError('Saved design not listed')
        for action, data, expected in [
            ('save', {'name': name, 'workspace': workspace}, 409),
            ('delete', {'name': name}, 400),
        ]:
            try:
                request(action, data)
                raise RuntimeError('Design protection failed: ' + action)
            except urllib.error.HTTPError as error:
                if error.code != expected:
                    raise
        request('save', {'name': name, 'workspace': workspace, 'overwrite': True})
        request('delete', {'name': name, 'confirmed': True})
        created = False
        print('Sprite stage and named Save/Load/Delete checks passed through Apache.')
    finally:
        if created:
            path = Path('/var/www/html/blocks/data/designs') / (hashlib.sha256(name.encode()).hexdigest() + '.json')
            path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
