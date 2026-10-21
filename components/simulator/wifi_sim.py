"""In-memory WiFi_IoT protocol model; never opens network/serial connections."""
import math


class WiFiModel:
    TYPES = {'0': 'int', '1': 'float', '2': 'bool', '3': 'string'}

    def __init__(self):
        self.fields = dict(S='', P='', M='1', U='', D='', K='')
        self.slots = {}
        self.last_reset = ''

    def status(self, scene):
        wifi = bool(scene.get('wifi_link', True) and self.fields['S'])
        cloud = bool(wifi and scene.get('cloud_link', True) and all(self.fields[key] for key in ['U', 'D', 'K']))
        return (3 if wifi else 0, 1 if cloud else 0)

    def set_slot(self, index, kind, value):
        index, kind = int(index), str(kind)
        if index not in range(4) or kind not in self.TYPES:
            raise ValueError('IoT index must be 0..3 with a supported type.')
        text = str(value)
        if not text.isascii() or len(text) > 40:
            raise ValueError('IoT values must be ASCII, at most 40 characters.')
        if kind == '0':
            text = str(int(text))
        elif kind == '1':
            number = float(text)
            if not math.isfinite(number):
                raise ValueError('IoT float must be finite.')
            text = str(number)
        elif kind == '2':
            if text.lower() not in ['true', 'false', '1', '0']:
                raise ValueError('IoT bool must be true or false.')
            text = 'true' if text.lower() in ['true', '1'] else 'false'
        self.slots[f'{kind}:{index}'] = text

    def packet(self, packet, scene):
        if not isinstance(packet, str) or not packet.isascii() or len(packet) > 53:
            raise ValueError('Invalid WiFi/IoT command')
        if packet.startswith('CN@@WIFI@@'):
            field, length, value = packet[10], int(packet[11:13]), packet[13:]
            if field not in self.fields or length != len(value) or length > 40:
                raise ValueError('Invalid WiFi/IoT settings')
            self.fields[field] = value
            return f'CN@@WOK@@{field}1'.ljust(20, '_')
        if packet.startswith('CN@@WRST@@'):
            reset = packet[10]
            if reset not in ['W', 'D', 'E']:
                raise ValueError('Unsupported simulated reset')
            self.last_reset = reset
            return f'CN@@WOK@@{reset}1'.ljust(20, '_')
        if packet.startswith('CN@@WSTAT@@'):
            wifi, cloud = self.status(scene)
            return f'CN@@WSTAT@@{wifi:02d}{cloud:02d}'.ljust(20, '_')
        if packet.startswith('CN@@WCRED@@'):
            step = int(packet[11:13])
            values = [self.fields[key] for key in ['S', 'P', 'D', 'K', 'U']] + ['sim-esp', 'sim-stm', 'sim-lib']
            if step not in range(8):
                raise ValueError('Invalid credential index')
            return f'CN@@WCRED@@{step:02d}' + values[step].ljust(40, '_')
        if packet.startswith('CN@@IOTW@@'):
            kind, index = packet[10], int(packet[11])
            length, value = int(packet[12:14]), packet[14:]
            if length != len(value):
                raise ValueError('Invalid IoT payload length')
            accepted = self.status(scene)[1] == 1
            if accepted:
                self.set_slot(index, kind, value)
            return f'CN@@IOK@@{kind}{index}{int(accepted)}'.ljust(20, '_')
        if packet.startswith('CN@@IOTR@@'):
            kind, index = packet[10], int(packet[11])
            if kind not in self.TYPES or index not in range(4):
                raise ValueError('Invalid IoT variable')
            value = self.slots.get(f'{kind}:{index}', {'0':'0', '1':'0.0', '2':'false', '3':''}[kind])
            # Current CodyNick.py reads a 20-byte frame: six bytes remain for data.
            value = value[:6] if self.status(scene)[1] else ''
            return f'CN@@IOTR@@{kind}{index}{len(value):02d}{value}'.ljust(20, '_')
        raise ValueError('Unsupported simulated WiFi/IoT command')

    def snapshot(self, scene):
        wifi, cloud = self.status(scene)
        return {'wifi': wifi, 'iot': cloud, 'ssid': self.fields['S'], 'device_id': self.fields['D'],
                'slots': [{'index': int(key[2:]), 'type': self.TYPES[key[0]], 'value': value}
                          for key, value in sorted(self.slots.items())], 'last_reset': self.last_reset}
