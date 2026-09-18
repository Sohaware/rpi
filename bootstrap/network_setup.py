#!/usr/bin/env python3
"""CodyNick network bootstrap. Application installation is a separate phase."""
import argparse
import copy
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

VERSION = "0.1.1"
STATE = Path('/var/lib/codynick/network-setup.json')
BASE = Path('/etc/codynick')
SELF = '/usr/local/lib/codynick/network_setup.py'
AP_ADDRESS = '10.42.0.1'
SERVICES = ['codynick-ap.service', 'codynick-dhcp.service', 'codynick-nat.service']

def run(*args, check=True, capture=False):
    return subprocess.run(args, check=check, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)

def active(name):
    return run('systemctl', 'is-active', '--quiet', name, check=False).returncode == 0

def write(path, text, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.new')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    os.chmod(tmp, mode)
    os.replace(tmp, path)

def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save(state):
    write(STATE, json.dumps(state, indent=2) + '\n')

def snapshot(state, path):
    path = Path(path)
    key = str(path)
    if key in state['files']:
        return
    if path.is_symlink():
        raise RuntimeError(f'Refusing to replace configuration symlink: {path}')
    target = Path(state['backup']) / key.lstrip('/')
    state['files'][key] = path.exists()
    if path.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    save(state)

def managed_write(state, path, text, mode=0o600):
    snapshot(state, path)
    write(path, text, mode)

def yaml_module():
    import yaml
    return yaml

def configs():
    yaml = yaml_module()
    return {p: yaml.safe_load(p.read_text()) or {} for p in sorted(Path('/etc/netplan').glob('*.yaml'))}

def choose_interfaces(records):
    onboard = [x['name'] for x in records if x['wifi'] and not x['usb']]
    usb = [x['name'] for x in records if x['wifi'] and x['usb']]
    wired = [x['name'] for x in records if not x['wifi'] and x['physical']]
    if len(onboard) != 1:
        raise RuntimeError('Expected exactly one built-in Wi-Fi adapter; no network changes made.')
    if len(usb) > 1:
        raise RuntimeError('Connect only one USB Wi-Fi adapter for this setup trial.')
    return onboard[0], usb, wired

def interfaces():
    records = []
    for p in Path('/sys/class/net').iterdir():
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', p.name):
            continue
        dev = (p / 'device').resolve()
        records.append(dict(name=p.name, wifi=(p / 'wireless').exists(),
                            physical=(p / 'device').exists(),
                            usb=any(re.fullmatch(r'usb\d+', part) for part in dev.parts)))
    return choose_interfaces(records)

def dongle_config(country):
    return {'renderer': 'networkd', 'optional': True, 'dhcp4': True,
            'dhcp6': False, 'accept-ra': False,
            'dhcp4-overrides': {'route-metric': 700},
            'regulatory-domain': country,
            'access-points': {'codynick': {'password': 'codynick'}}}

def remove_wifi(doc, names):
    result = copy.deepcopy(doc)
    wifi = result.get('network', {}).get('wifis', {})
    for name in names:
        wifi.pop(name, None)
    return result

def internet(interface):
    # Binding the socket to the device prevents the built-in Wi-Fi hiding a failure.
    r = run('curl', '--interface', interface, '-4', '--fail', '--silent',
            '--show-error', '--connect-timeout', '8', '--max-time', '20',
            '--output', '/dev/null', 'https://github.com/Sohaware/rpi',
            check=False, capture=True)
    return r.returncode == 0

def prepare_dongle(state, docs):
    usb = state['usb']
    if not usb:
        return
    name = usb[0]
    definitions = [doc.get('network', {}).get('wifis', {}).get(name)
                   for doc in docs.values()]
    definitions = [cfg for cfg in definitions if cfg is not None]
    desired = dongle_config(state['country'])
    if definitions == [desired] and internet(name):
        print('USB Wi-Fi already configured and online; leaving its connection intact.', flush=True)
        return
    yaml = yaml_module()
    for p, doc in docs.items():
        new = remove_wifi(doc, usb)
        if new != doc:
            managed_write(state, p, yaml.safe_dump(new, sort_keys=False))
    managed_write(state, '/etc/netplan/90-codynick-usb.yaml', yaml.safe_dump(
        {'network': {'version': 2, 'wifis': {name: desired}}}, sort_keys=False))
    run('netplan', 'generate')
    # A global netplan apply can drop the SSH-bearing built-in Wi-Fi. Only reload
    # generated definitions and restart the detected USB adapter's supplicant.
    run('systemctl', 'daemon-reload')
    run('systemctl', 'restart', f'netplan-wpa-{name}.service')
    run('networkctl', 'reload')
    run('networkctl', 'reconfigure', name)

def arm_rollback():
    write('/etc/systemd/system/codynick-rollback.service',
          '[Unit]\nDescription=Restore unconfirmed CodyNick network\nAfter=network.target\n'
          f'[Service]\nType=oneshot\nExecStart=/usr/bin/python3 {SELF} --rollback\n', 0o644)
    write('/etc/systemd/system/codynick-rollback.timer',
          '[Unit]\nDescription=Rollback CodyNick hotspot unless confirmed\n'
          '[Timer]\nOnActiveSec=15min\nOnUnitInactiveSec=1min\nAccuracySec=1s\n'
          '[Install]\nWantedBy=timers.target\n', 0o644)
    run('systemctl', 'daemon-reload')
    run('systemctl', 'enable', 'codynick-rollback.timer')
    run('systemctl', 'restart', 'codynick-rollback.timer')

def show(state):
    print(f'CodyNick network bootstrap {VERSION}', flush=True)
    print('Stage:', state.get('stage', 'not started'))
    if state.get('ssid'):
        print('Hotspot:', state['ssid'])
        print('Password: CodyNick12345')
        print(f"Reconnect: ssh {state['login']}@{AP_ADDRESS}")
    print('Application installer: not included in this network trial')

def preflight():
    if os.geteuid() != 0:
        raise RuntimeError('Run using sudo.')
    osinfo = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if osinfo.get('ID', '').strip('"') != 'ubuntu' or osinfo.get('VERSION_ID', '').strip('"') != '26.04':
        raise RuntimeError('This trial supports Ubuntu 26.04 only.')
    if platform.machine() != 'aarch64':
        raise RuntimeError('This trial requires ARM64.')

def check_network():
    state = load()
    show(state)
    run('ip', '-br', 'address')
    for service in ['ssh', *SERVICES]:
        print(f'{service}: {"active" if active(service) else "inactive"}')

def rollback():
    state = load()
    if state.get('stage') not in ('preparing', 'pending', 'applying'):
        return
    print('Restoring network configuration before hotspot handover.', flush=True)
    for service in SERVICES:
        run('systemctl', 'disable', '--now', service, check=False)
    run('nft', 'delete', 'table', 'ip', 'codynick_setup', check=False)
    for path, existed in state['files'].items():
        p = Path(path)
        if existed:
            shutil.copy2(Path(state['backup']) / path.lstrip('/'), p)
        else:
            p.unlink(missing_ok=True)
    run('sysctl', '-w', 'net.ipv4.ip_forward=' + state['previous_forwarding'], check=False)
    run('systemctl', 'daemon-reload')
    run('netplan', 'generate')
    run('netplan', 'apply')
    state['stage'] = 'rolled-back'
    save(state)
    run('systemctl', 'disable', '--now', 'codynick-rollback.timer', check=False)
    print('Previous network restored. Rerun sudo codynick-setup to retry.', flush=True)

def apply_handover():
    state = load()
    if state.get('stage') != 'pending':
        raise RuntimeError('No prepared handover.')
    try:
        state['stage'] = 'applying'
        save(state)
        yaml = yaml_module()
        for p, doc in configs().items():
            new = remove_wifi(doc, [state['ap']])
            if new != doc:
                managed_write(state, p, yaml.safe_dump(new, sort_keys=False))
        managed_write(state, '/etc/cloud/cloud.cfg.d/99-codynick-network.cfg',
                      'network: {config: disabled}\n')
        # AP is a plain networkd link; hostapd owns its radio, not wpa_supplicant.
        managed_write(state, '/etc/systemd/network/05-codynick-ap.network',
                      f"[Match]\nName={state['ap']}\n\n[Network]\nAddress={AP_ADDRESS}/24\n"
                      'DHCP=no\nLinkLocalAddressing=no\nConfigureWithoutCarrier=yes\n'
                      '\n[Link]\nRequiredForOnline=no\n', 0o644)
        run('netplan', 'generate')
        run('netplan', 'apply')
        run('networkctl', 'reload')
        run('networkctl', 'reconfigure', state['ap'])
        run('sysctl', '-w', 'net.ipv4.ip_forward=1')
        for service in SERVICES:
            run('systemctl', 'enable', '--now', service)
        time.sleep(5)
        if not all(active(s) for s in SERVICES):
            raise RuntimeError('Hotspot services did not start.')
        print('Hotspot active. Awaiting user confirmation; rollback in 15 minutes.', flush=True)
    except Exception:
        rollback()
        raise

def confirm():
    state = load()
    if state.get('stage') != 'applying':
        raise RuntimeError('No hotspot handover awaiting confirmation.')
    if not all(active(s) for s in SERVICES):
        raise RuntimeError('Hotspot services are not all active. Rollback remains armed.')
    ssh = os.environ.get('SSH_CONNECTION', '').split()
    if ssh and (len(ssh) != 4 or ssh[2] != AP_ADDRESS):
        raise RuntimeError('Reconnect by SSH to 10.42.0.1 before confirming.')
    if input('Are you connected to the CodyNick hotspot and able to use SSH? [y/N] ').strip().lower() != 'y':
        return
    if not any(internet(n) for n in state['uplinks']):
        raise RuntimeError('Alternative internet check failed. Rollback remains armed.')
    state['stage'] = 'network-ready'
    state['confirmed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    save(state)
    run('systemctl', 'disable', '--now', 'codynick-rollback.timer')
    show(state)
    print('Network stage verified. Keep this SD card; application installation follows separately.')

def prepare():
    state = load()
    if state.get('stage') == 'network-ready':
        check_network()
        return
    if state.get('stage') in ('pending', 'applying'):
        show(state)
        print('Run sudo codynick-setup --confirm after joining the hotspot.')
        return
    if state.get('stage') == 'preparing':
        rollback()
        raise RuntimeError('Interrupted preparation restored. Rerun to try again.')
    if not active('systemd-networkd') or active('NetworkManager'):
        raise RuntimeError('This first trial requires systemd-networkd without NetworkManager.')
    if not active('systemd-resolved'):
        raise RuntimeError('This trial requires systemd-resolved for hotspot DNS forwarding.')
    if active('hostapd') or active('dnsmasq') or Path('/root/codynick/service.py').exists():
        raise RuntimeError('Existing CodyNick/hotspot installation: use a future migration release, not this fresh-OS trial.')
    ufw = Path('/etc/ufw/ufw.conf')
    if ufw.exists() and re.search(r'^ENABLED=yes$', ufw.read_text(), re.M):
        raise RuntimeError('Active UFW needs a reviewed hotspot rule set before this trial.')
    login = os.environ.get('SUDO_USER', '')
    if not login or login == 'root':
        raise RuntimeError('Log in as your existing administrator and invoke this command with sudo.')
    import pwd
    pwd.getpwnam(login)
    ap, usb, wired = interfaces()
    if not wired and not usb:
        raise RuntimeError('Connect Ethernet or a supported USB Wi-Fi adapter first.')
    run('apt-get', 'update')
    run('apt-get', 'install', '-y', 'python3-yaml', 'curl', 'hostapd', 'dnsmasq-base',
        'nftables', 'openssh-server', 'iw', 'net-tools')
    docs = configs()
    country = None
    for doc in docs.values():
        wifi = doc.get('network', {}).get('wifis', {})
        for name, cfg in wifi.items():
            if 'match' in cfg or 'set-name' in cfg:
                raise RuntimeError('Wi-Fi match/rename configuration needs review before this trial.')
            if cfg.get('renderer') not in (None, 'networkd'):
                raise RuntimeError('Mixed network managers are unsupported in this trial.')
            if name == ap:
                country = cfg.get('regulatory-domain')
    if not country:
        country = input('Two-letter Wi-Fi country code (your actual location): ').strip().upper()
    if not re.fullmatch('[A-Z]{2}', str(country)):
        raise RuntimeError('Invalid Wi-Fi country code.')
    serial_file = Path('/sys/firmware/devicetree/base/serial-number')
    serial = serial_file.read_text().strip('\x00\n') if serial_file.exists() else ''
    if not re.fullmatch('[0-9a-fA-F]{8,32}', serial):
        raise RuntimeError('Could not identify Raspberry Pi hardware serial.')
    ssid = 'codynick-' + serial[-8:].lower()
    routes = json.loads(run('ip', '-j', '-4', 'route', 'show', 'table', 'all', capture=True).stdout)
    subnet = ipaddress.ip_network('10.42.0.0/24')
    for route in routes:
        dest = route.get('dst', 'default')
        if dest != 'default' and subnet.overlaps(ipaddress.ip_network(dest, strict=False)):
            raise RuntimeError('Existing route overlaps 10.42.0.0/24. Network needs review.')
    phy = Path('/sys/class/net', ap, 'phy80211').resolve().name
    info = run('iw', 'phy', phy, 'info', capture=True).stdout
    if not re.search(r'^\s*\* AP\s*$', info, re.M):
        raise RuntimeError('Built-in adapter does not advertise AP support.')
    Path('/run/sshd').mkdir(mode=0o755, exist_ok=True)
    run('/usr/sbin/sshd', '-t')
    sshcfg = run('/usr/sbin/sshd', '-T', capture=True).stdout
    if 'port 22\n' not in sshcfg or 'listenaddress 0.0.0.0:22' not in sshcfg:
        raise RuntimeError('SSH must listen on all IPv4 addresses on port 22 for this trial.')
    run('systemctl', 'enable', '--now', 'ssh')
    print(f'Built-in Wi-Fi: {ap}; USB: {usb}; Ethernet: {wired}')
    print('Phase 1 only: prepare hotspot/SSH. No application deployment or root-password changes.')
    if input('Prepare this network handover? [y/N] ').strip().lower() != 'y':
        return
    backup = Path('/var/backups/codynick/network-' + time.strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True, mode=0o700)
    state = dict(version=VERSION, stage='preparing', backup=str(backup), files={},
                 ap=ap, usb=usb, wired=wired, login=login, ssid=ssid, country=country,
                 previous_forwarding=Path('/proc/sys/net/ipv4/ip_forward').read_text().strip())
    save(state)
    try:
        arm_rollback()
        prepare_dongle(state, docs)
        uplinks = []
        for attempt in range(3):
            uplinks = [n for n in wired + usb if internet(n)]
            if uplinks:
                break
            time.sleep(5)
        if not uplinks:
            raise RuntimeError('Neither Ethernet nor the dongle can reach GitHub over HTTPS. Built-in Wi-Fi will stay unchanged.')
        state['uplinks'] = uplinks
        save(state)
        configure_services(state)
        show(state)
        print('Verified internet adapters:', ', '.join(uplinks))
        print('Use your EXISTING administrator password or SSH key; no new login is created.')
        print('After switching, reconnect and run: sudo codynick-setup --confirm')
        print('Without confirmation within 15 minutes, the previous network will be restored.')
        if input('Switch to the hotspot now? [y/N] ').strip().lower() != 'y':
            rollback()
            return
        state['stage'] = 'pending'
        save(state)
        arm_rollback()
        run('systemd-run', '--unit=codynick-network-handover', '--collect', '--on-active=10s',
            '/usr/bin/python3', SELF, '--apply')
        print('Switch scheduled in 10 seconds. Join the hotspot, then confirm. No reboot required.', flush=True)
    except Exception:
        rollback()
        raise

def configure_services(state):
    ap = state['ap']
    # Ethernet first, USB second; keep the original built-in connection until handover.
    override = {'network': {'version': 2, 'ethernets': {}, 'wifis': {}}}
    for name in state['wired']:
        override['network']['ethernets'][name] = {'optional': True, 'dhcp4': True,
            'dhcp4-overrides': {'route-metric': 100}, 'dhcp6-overrides': {'route-metric': 100}}
    for name in state['usb']:
        override['network']['wifis'][name] = {'dhcp4-overrides': {'route-metric': 200}}
    managed_write(state, '/etc/netplan/95-codynick-route-priority.yaml',
                  yaml_module().safe_dump(override, sort_keys=False))
    run('netplan', 'generate')
    managed_write(state, BASE / 'hostapd.conf',
                  f"interface={ap}\ndriver=nl80211\nssid={state['ssid']}\ncountry_code={state['country']}\n"
                  'hw_mode=g\nchannel=6\nieee80211d=1\nwmm_enabled=1\nauth_algs=1\n'
                  'wpa=2\nwpa_passphrase=CodyNick12345\nwpa_key_mgmt=WPA-PSK\nrsn_pairwise=CCMP\n')
    managed_write(state, BASE / 'dnsmasq.conf',
                  f'interface={ap}\nbind-dynamic\nlisten-address={AP_ADDRESS}\n'
                  'dhcp-range=10.42.0.50,10.42.0.200,255.255.255.0,24h\n'
                  f'dhcp-option=3,{AP_ADDRESS}\ndhcp-option=6,{AP_ADDRESS}\n'
                  'no-resolv\nserver=127.0.0.53\n'
                  f'address=/start.codynick/{AP_ADDRESS}\n')
    names = ', '.join('"' + n + '"' for n in state['wired'] + state['usb'])
    managed_write(state, BASE / 'nat.nft',
                  'table ip codynick_setup {\n chain postrouting {\n'
                  '  type nat hook postrouting priority srcnat; policy accept;\n'
                  f'  ip saddr 10.42.0.0/24 oifname {{ {names} }} masquerade\n'
                  ' }\n}\n', 0o600)
    run('nft', '--check', '--file', str(BASE / 'nat.nft'))
    managed_write(state, '/etc/sysctl.d/90-codynick-forward.conf', 'net.ipv4.ip_forward=1\n', 0o644)
    commands = {
        'codynick-ap.service': '/usr/sbin/hostapd /etc/codynick/hostapd.conf',
        'codynick-dhcp.service': '/usr/sbin/dnsmasq --keep-in-foreground --conf-file=/etc/codynick/dnsmasq.conf',
        'codynick-nat.service': '/usr/sbin/nft --file /etc/codynick/nat.nft',
    }
    for name, cmd in commands.items():
        nat = name == 'codynick-nat.service'
        extra = ('RemainAfterExit=yes\nExecStartPre=-/usr/sbin/nft delete table ip codynick_setup\n'
                 'ExecStop=-/usr/sbin/nft delete table ip codynick_setup\n') if nat else 'Restart=on-failure\nRestartSec=3\n'
        managed_write(state, '/etc/systemd/system/' + name,
                      '[Unit]\nDescription=CodyNick network bootstrap\nAfter=systemd-networkd.service\n'
                      f'\n[Service]\nType={"oneshot" if nat else "simple"}\nExecStart={cmd}\n{extra}'
                      '\n[Install]\nWantedBy=multi-user.target\n', 0o644)
    run('dnsmasq', '--test', '--conf-file=' + str(BASE / 'dnsmasq.conf'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    for flag in ('check', 'confirm', 'rollback', 'apply', 'version'):
        group.add_argument('--' + flag, action='store_true')
    args = parser.parse_args()
    if args.version:
        print(VERSION)
        return
    preflight()
    import fcntl
    with open('/run/lock/codynick-network.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.check: check_network()
        elif args.confirm: confirm()
        elif args.rollback: rollback()
        elif args.apply: apply_handover()
        else: prepare()

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
