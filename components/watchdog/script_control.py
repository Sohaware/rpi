#!/usr/bin/python3
"""Privileged, fixed-action control of the student script only."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import socket
import struct
import sys

STOPPED = Path('/run/codynick-script-stopped')


def control(action):
    if action not in ('start', 'stop'):
        raise ValueError('Only start and stop are allowed.')
    with open('/run/lock/codynick-script-control.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action == 'stop':
            STOPPED.touch(mode=0o644)
            subprocess.run(['systemctl', 'stop', 'script.service'], check=True, timeout=20)
        else:
            with open('/home/client/active_script.py', 'rb') as script:
                fcntl.flock(script, fcntl.LOCK_SH)
                digest = hashlib.sha256(script.read()).hexdigest()
            STOPPED.unlink(missing_ok=True)
            subprocess.run(['systemctl', 'restart', 'script.service'], check=True, timeout=20)
            Path('/root/codynick/hash.txt').write_text(digest + '\n')


def handle_client(client, allowed_uids):
    client.settimeout(3)
    try:
        _, uid, _ = struct.unpack('3i', client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid not in allowed_uids:
            raise PermissionError('Client is not permitted.')
        request = b''
        while b'\n' not in request and len(request) < 16:
            chunk = client.recv(16 - len(request))
            if not chunk:
                break
            request += chunk
        if request not in (b'start\n', b'stop\n'):
            raise ValueError('Only start and stop are allowed.')
        action = request.decode('ascii').strip()
        control(action)
        result = {'ok': True, 'state': 'stopped' if action == 'stop' else 'running'}
    except Exception as error:
        result = {'ok': False, 'error': str(error)}
    try:
        client.sendall((json.dumps(result) + '\n').encode())
    except OSError:
        pass


def main():
    if os.geteuid() != 0:
        raise SystemExit('Root service required.')
    if sys.argv[1:] == ['--serve']:
        import pwd
        if os.environ.get('LISTEN_PID') != str(os.getpid()) or os.environ.get('LISTEN_FDS') != '1':
            raise SystemExit('A systemd socket is required.')
        allowed_uids = {0, pwd.getpwnam('www-data').pw_uid}
        with socket.socket(fileno=3) as listener:
            while True:
                client, _ = listener.accept()
                with client:
                    handle_client(client, allowed_uids)
    elif sys.argv[1:] in (['start'], ['stop']):
        control(sys.argv[1])
    else:
        raise SystemExit('Usage: codynick-script-control start|stop|--serve')


if __name__ == '__main__':
    main()
