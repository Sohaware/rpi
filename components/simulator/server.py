"""Isolated CodyJoy Pro simulator; no serial access or code execution endpoints."""
import argparse
import hmac
import json
import math
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import parse_qs, urlsplit
from wifi_sim import WiFiModel

ROOT = Path(__file__).resolve().parent


def display_number(raw):
    """Fit the numeric wire payload to four digits, including a minus sign."""
    value = float(raw)
    if not math.isfinite(value) or value < -999 or value > 9999:
        return '----'
    # The Python API has already limited the wire text to five characters.
    places = max(0, 4 - len(str(abs(int(value)))) - int(value < 0))
    factor = 10 ** places
    value = math.trunc(value * factor) / factor
    text = f'{value:.{places}f}'
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    if text == '-0':
        text = '0'
    return text if len(text.replace('.', '')) <= 4 else '----'


class State:
    def __init__(self, scene_file=None):
        self.lock = threading.Lock()
        self.session = None
        self.seen = 0
        self.input_seen = 0
        self.inputs = []
        self.joystick_seen = 0
        self.joystick_inputs = []
        self.leds = ['#000000'] * 16
        self.notes = []
        self.sequence = 0
        self.seven_segment = ''
        self.scene_file = scene_file
        self.scene = {'gadgets': {'cjp': {'x': 40, 'y': 40}}, 'temperature': 21.1}
        self.matrix = {'text': '', 'speed': 1, 'pixels': [0] * 64, 'mode': 'pixels', 'revision': 0}
        self.error = ''
        self.wifi = WiFiModel()
        if scene_file and scene_file.exists():
            saved = json.loads(scene_file.read_text())
            # Older prototypes stored raw soil readings; retain their layout.
            if isinstance(saved, dict) and isinstance(saved.get('soil'), (int, float)) and saved['soil'] > 100:
                saved['soil'] = 100
            self.scene = self.validate_scene(saved)

    @staticmethod
    def validate_scene(scene):
        if not isinstance(scene, dict) or not isinstance(scene.get('gadgets'), dict):
            raise ValueError('Invalid stage layout')
        gadgets = scene['gadgets']
        if 'cjp' not in gadgets or any(key not in ['cjp', 'seven', 'temperature', 'matrix', 'joystick', 'ultrasonic', 'soil', 'wifi'] for key in gadgets):
            raise ValueError('The stage must contain CodyJoy Pro and supported gadgets only.')
        clean = {}
        for key, pos in gadgets.items():
            x, y = float(pos['x']), float(pos['y'])
            if not math.isfinite(x) or not math.isfinite(y) or not 0 <= x <= 1400 or not 0 <= y <= 1500:
                raise ValueError('Invalid gadget position')
            clean[key] = {'x': x, 'y': y}
        temperature = float(scene.get('temperature', 21.1))
        if not math.isfinite(temperature) or not -55 <= temperature <= 125:
            raise ValueError('Temperature must be between -55 and 125 C.')
        result = {'gadgets': clean, 'temperature': round(temperature, 1)}
        for key, default, low, high in [('distance', 50, 2, 400), ('soil', 50, 0, 100)]:
            number = float(scene.get(key, default))
            if not math.isfinite(number) or not low <= number <= high:
                raise ValueError(f'{key} must be between {low} and {high}.')
            result[key] = round(number, 1)
        for key in ['wifi_link', 'cloud_link']:
            value = scene.get(key, True)
            if not isinstance(value, bool):
                raise ValueError('Network availability must be true or false.')
            result[key] = value
        return result

    def save_scene(self, scene):
        clean = self.validate_scene(scene)
        if self.scene_file:
            temporary = self.scene_file.with_suffix('.tmp')
            temporary.write_text(json.dumps(clean, indent=2) + '\n')
            temporary.replace(self.scene_file)
        if 'seven' not in clean['gadgets']:
            self.seven_segment = ''
        if 'matrix' not in clean['gadgets']:
            self.matrix.update(text='', pixels=[0] * 64, mode='pixels', revision=self.matrix['revision'] + 1)
        self.scene = clean
        self.error = ''

    def require(self, gadget):
        if gadget not in self.scene['gadgets']:
            names = {'seven': 'Seven-segment display', 'temperature': 'Temperature sensor', 'matrix': 'LED matrix', 'joystick': 'Stand-Alone joystick', 'ultrasonic': 'Ultrasonic sensor', 'soil': 'Soil-moisture sensor', 'wifi': 'Wi-Fi/IoT gadget'}
            self.error = f"Add {names[gadget]} to the stage, then run the Python script again."
            raise ValueError(self.error)

    def expire(self):
        now = time.monotonic()
        if now - self.input_seen > 1:
            self.inputs = []
        if now - self.joystick_seen > 1:
            self.joystick_inputs = []
        if self.session and now - self.seen > 3:
            self.session = None
            self.leds = ['#000000'] * 16
            self.inputs = []
            self.joystick_inputs = []
            self.notes = []

    def command(self, data):
        with self.lock:
            self.expire()
            action = data.get('action')
            if action == 'scene':
                if self.session:
                    # Arrange freely, but stop Python before changing its hardware set.
                    if set(data['scene']['gadgets']) != set(self.scene['gadgets']):
                        raise ValueError('Stop the Python script before adding or removing gadgets.')
                self.save_scene(data['scene'])
                return {}
            if action == 'open':
                if self.session:
                    raise ValueError('Another Python script is using the simulator. Stop it first.')
                self.session = secrets.token_hex(16)
                self.seen = time.monotonic()
                self.leds = ['#000000'] * 16
                self.notes = []
                self.error = ''
                return {'session': self.session}
            if action == 'input':
                values = data.get('states', [])
                if not isinstance(values, list) or any(v not in ['UP', 'DOWN', 'LEFT', 'RIGHT', 'CLICK'] for v in values):
                    raise ValueError('Invalid joystick states')
                device = data.get('device', 'cjp')
                if device == 'joystick':
                    self.require('joystick')
                    self.joystick_inputs = values
                    self.joystick_seen = time.monotonic()
                elif device == 'cjp':
                    self.inputs = values
                    self.input_seen = time.monotonic()
                else:
                    raise ValueError('Invalid joystick device')
                return {}
            if action == 'wifi_slot':
                self.require('wifi')
                self.wifi.set_slot(data['index'], str(data['type']), data['value'])
                return {}
            if not self.session or data.get('session') != self.session:
                raise ValueError('Simulator connection expired; restart the Python script.')
            self.seen = time.monotonic()
            if action == 'led':
                index = int(data['index'])
                color = data['color']
                if not 0 <= index <= 15 or not isinstance(color, str) or len(color) != 7 or color[0] != '#':
                    raise ValueError('Invalid LED')
                int(color[1:], 16)
                self.leds[index] = color
            elif action == 'clear':
                self.leds = ['#000000'] * 16
            elif action == 'seven_segment':
                self.require('seven')
                if data.get('device') != 0:
                    raise ValueError('Only the Stand-Alone seven-segment display is supported.')
                self.seven_segment = display_number(data['value'])
            elif action == 'temperature':
                self.require('temperature')
                return {'temperature': self.scene['temperature']}
            elif action == 'joystick':
                self.require('joystick')
                return {'states': self.joystick_inputs[:]}
            elif action == 'ultrasonic':
                self.require('ultrasonic')
                if data.get('device') != 0:
                    raise ValueError('Only the Stand-Alone ultrasonic sensor is supported.')
                return {'value': self.scene.get('distance', 50)}
            elif action == 'soil':
                self.require('soil')
                return {'value': self.scene.get('soil', 50)}
            elif action == 'wifi_packet':
                self.require('wifi')
                return {'response': self.wifi.packet(data['packet'], self.scene)}
            elif action == 'matrix_text':
                self.require('matrix')
                text, speed = data['text'], data['speed']
                if not isinstance(text, str) or not text.isascii() or len(text) > 49 or speed not in [0, 1, 2]:
                    raise ValueError('Invalid LED matrix text or speed')
                self.matrix.update(text=text, speed=speed, mode='text', revision=self.matrix['revision'] + 1)
            elif action == 'matrix_pixel':
                self.require('matrix')
                x, y, value = int(data['x']), int(data['y']), int(data['value'])
                if not 0 <= x <= 7 or not 0 <= y <= 7 or value not in [0, 1]:
                    raise ValueError('Invalid LED matrix pixel')
                if self.matrix['mode'] != 'pixels':
                    self.matrix['pixels'] = [0] * 64
                self.matrix['pixels'][y * 8 + x] = value
                self.matrix.update(mode='pixels', revision=self.matrix['revision'] + 1)
            elif action == 'matrix_clear':
                self.require('matrix')
                self.matrix.update(text='', pixels=[0] * 64, mode='pixels', revision=self.matrix['revision'] + 1)
            elif action == 'note':
                frequency, duration = int(data['frequency']), int(data['duration'])
                if not 20 <= frequency <= 20000 or not 1 <= duration <= 99999:
                    raise ValueError('Invalid note')
                self.sequence += 1
                self.notes.append({'id': self.sequence, 'frequency': frequency, 'duration': duration, 'at': time.time()})
                self.notes = self.notes[-64:]
            elif action == 'close':
                self.session = None
                self.inputs = []
                self.joystick_inputs = []
                self.leds = ['#000000'] * 16
                self.notes = []
            elif action != 'heartbeat':
                raise ValueError('Unsupported simulator command')
            return {'states': self.inputs}

    def snapshot(self):
        with self.lock:
            self.expire()
            return {'leds': self.leds[:], 'notes': self.notes[:], 'states': self.inputs[:], 'joystick_states': self.joystick_inputs[:], 'wifi': self.wifi.snapshot(self.scene), 'connected': bool(self.session), 'now': time.time(), 'seven_segment': self.seven_segment, 'scene': self.validate_scene(self.scene), 'matrix': json.loads(json.dumps(self.matrix)), 'error': self.error, 'prototype': 'stage-4'}


def handler(token, state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Do not write access tokens to request logs.

        def authenticated(self):
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get('Cookie', ''))
                value = cookie['sim_token'].value if 'sim_token' in cookie else ''
            except Exception:
                value = ''
            bearer = self.headers.get('Authorization', '').removeprefix('Bearer ')
            return any(hmac.compare_digest(v, token) for v in [value, bearer])

        def reply(self, status, content, kind='application/json', cookie=False):
            raw = content if isinstance(content, bytes) else json.dumps(content).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            if cookie:
                self.send_header('Set-Cookie', f'sim_token={token}; HttpOnly; SameSite=Strict; Path=/')
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            url = urlsplit(self.path)
            supplied = parse_qs(url.query).get('token', [''])[0]
            entry = url.path == '/' and hmac.compare_digest(supplied, token)
            if not entry and not self.authenticated():
                return self.reply(401, {'error': 'Open the simulator using the private URL printed by the installer.'})
            if url.path == '/':
                return self.reply(200, (ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8', entry)
            if url.path == '/state':
                return self.reply(200, state.snapshot())
            if url.path in ['/app.js', '/font5x7.js', '/style.css', '/gadget.svg', '/seven-segment.svg', '/sensor.svg', '/sensor.png', '/matrix.svg', '/joystick.png', '/ultrasonic.png', '/soil.png', '/wifi.png']:
                kind = {'/app.js': 'text/javascript', '/font5x7.js': 'text/javascript', '/style.css': 'text/css', **{p: 'image/png' for p in ['/sensor.png', '/joystick.png', '/ultrasonic.png', '/soil.png', '/wifi.png']}}
                return self.reply(200, (ROOT / url.path[1:]).read_bytes(), kind.get(url.path, 'image/svg+xml'))
            return self.reply(404, {'error': 'Not found'})

        def do_POST(self):
            if not self.authenticated():
                return self.reply(401, {'error': 'Unauthorized'})
            # JSON-only requests and no CORS support prevent cross-site form writes.
            if self.path != '/command' or self.headers.get('Content-Type') != 'application/json':
                return self.reply(400, {'error': 'Expected JSON command'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Expected object')
                self.reply(200, state.command(data))
            except (ValueError, KeyError, TypeError) as exc:
                self.reply(400, {'error': str(exc)})
            except OSError:
                self.reply(500, {'error': 'Cannot save stage layout. Rerun the local prototype installer to check permissions.'})
    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8091)
    parser.add_argument('--token-file', type=Path, required=True)
    parser.add_argument('--scene-file', type=Path)
    args = parser.parse_args()
    token = args.token_file.read_text().strip()
    if len(token) < 32:
        raise SystemExit('A private token of at least 32 characters is required.')
    print(f'CodyNick simulator prototype listening on {args.host}:{args.port}', flush=True)
    ThreadingHTTPServer((args.host, args.port), handler(token, State(args.scene_file))).serve_forever()
