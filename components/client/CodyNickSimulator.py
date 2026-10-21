"""Simulator transport for existing CodyNick gadget commands. No physical ports."""
import atexit
import json
import os
from pathlib import Path
import threading
import urllib.request
import urllib.error


class Simulator:
    def __init__(self):
        self.url = os.environ.get('CODYNICK_SIM_URL', 'http://127.0.0.1:8091')
        self.token = Path(os.environ.get('CODYNICK_SIM_TOKEN_FILE', '/opt/codynick-simulator/token')).read_text().strip()
        self.session = None
        self.ser = self
        self.response = ''
        self.buffer = b''
        self.error = None
        self.stop = threading.Event()
        self.session = self._request('open')['session']
        self.thread = threading.Thread(target=self._heartbeat, daemon=True)
        self.thread.start()
        atexit.register(self.close)
        print('[Simulator] Gadget stage connected. Physical hardware is not used.')

    def _request(self, action, **values):
        body = json.dumps(dict(action=action, session=self.session, **values)).encode()
        request = urllib.request.Request(self.url + '/command', data=body, headers={
            'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token})
        try:
            with urllib.request.urlopen(request, timeout=2) as reply:
                return json.load(reply)
        except urllib.error.HTTPError as exc:
            message = json.loads(exc.read()).get('error', str(exc))
            print('[Simulator] ' + message)
            raise RuntimeError(message) from exc

    def _heartbeat(self):
        while not self.stop.wait(0.5):
            try:
                self._request('heartbeat')
            except Exception as exc:
                self.error = exc
                return

    def ensure_connected(self):
        if self.error:
            raise RuntimeError('Simulator connection lost') from self.error
        return self.session is not None

    def flush(self):
        self.response = ''

    def reset_input_buffer(self):
        self.buffer = b''

    def read(self, size=1):
        value, self.buffer = self.buffer[:size], self.buffer[size:]
        return value

    def write(self, packet):
        text = packet.decode('ascii')
        if text.startswith('CN@@TEMP@@'):
            temperature = self._request('temperature')['temperature']
            self.buffer = ('CN@@TEMP@@' + str(temperature)).ljust(20, '_').encode('ascii')
        elif text.startswith('CN@@SOIL@@'):
            value = self._request('soil')['value']
            self.buffer = ('CN@@SOIL@@' + str(value)).ljust(20, '_').encode('ascii')
        elif text.startswith('CN@@ULTRA@@'):
            device = int(text[11:13])
            value = self._request('ultrasonic', device=device)['value']
            self.buffer = (f'CN@@ULTRA@@{device:02d}' + str(value)).ljust(20, '_').encode('ascii')
        elif text.startswith('CN@@LTXT@@'):
            speed, length = int(text[10]), int(text[11:13])
            value = text[13:]
            if len(value) != length:
                raise ValueError('Invalid LED matrix text length')
            self._request('matrix_text', text=value, speed=speed)
        else:
            self.send_line(text)
        return len(packet)

    def send_line(self, packet, add_newline=False):
        self.ensure_connected()
        if packet.startswith('CN@@RGB@@'):
            self._request('led', index=int(packet[9:11]), color=packet[11:18])
        elif packet.startswith('CN@@RGBCLR@@'):
            self._request('clear')
        elif packet.startswith('CN@@BUZ@@'):
            self._request('note', frequency=int(packet[9:13]), duration=int(packet[13:18]))
        elif packet.startswith('CN@@JOY@@'):
            device = int(packet[9:11])
            if device not in [0, 5]:
                raise ValueError('Only Stand-Alone and CJP joysticks are simulated.')
            values = self._request('heartbeat' if device == 5 else 'joystick')['states']
            letters = dict(UP='U', DOWN='D', LEFT='L', RIGHT='R', CLICK='C')
            self.response = (f'CN@@JOY@@{device:02d}' + (''.join(letters[v] for v in values) or 'N')).ljust(20, '_')
        elif packet.startswith('CN@@7SEG@@'):
            self._request('seven_segment', device=int(packet[10:12]), value=packet[12:].split('\0', 1)[0])
        elif packet.startswith('CN@@LPX@@'):
            self._request('matrix_pixel', x=int(packet[9]), y=int(packet[10]), value=int(packet[11]))
        elif packet.startswith('CN@@LCLR@@'):
            self._request('matrix_clear')
        elif packet.startswith(('CN@@WIFI@@', 'CN@@WRST@@', 'CN@@WSTAT@@', 'CN@@WCRED@@', 'CN@@IOTW@@', 'CN@@IOTR@@')):
            self.buffer = self._request('wifi_packet', packet=packet)['response'].encode('ascii')
        else:
            raise NotImplementedError('This gadget command is not supported by the simulator prototype.')

    def read_line(self, **kwargs):
        response, self.response = self.response, ''
        return response

    def record_io_success(self):
        pass

    def record_io_failure(self):
        raise RuntimeError('Unsupported or invalid simulator response')

    def mark_disconnected(self):
        self.close()

    def close(self):
        self.stop.set()
        if self.session:
            try:
                self._request('close')
            except Exception:
                pass
            self.session = None

    close_serial = close
