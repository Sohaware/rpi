"""Unprivileged local sprite state. No Python execution or hardware access."""
import json
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Stage:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = dict(x=0, y=0, direction=90, size=100, visible=True, speech='', backdrop='white')
        self.keys = []
        self.key_time = 0
        self.mouse = {'x': 0, 'y': 0, 'down': False}
        self.mouse_time = 0
        self.speech_until = 0

    @staticmethod
    def edge_limits(state):
        angle = math.radians(state['direction'])
        extent = 24 * state['size'] / 100 * (abs(math.cos(angle)) + abs(math.sin(angle)))
        return 240 - extent, 180 - extent

    @staticmethod
    def number(value, low, high):
        value = float(value)
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError('Number outside supported range')
        return value

    def command(self, data):
        with self.lock:
            action = data.get('action')
            state = dict(self.state)
            if action == 'configure' or action == 'begin':
                self.speech_until = 0
                state.update(x=self.number(data.get('x', 0), -240, 240),
                             y=self.number(data.get('y', 0), -180, 180),
                             direction=self.number(data.get('direction', 90), -36000, 36000) % 360,
                             visible=True, speech='')
                backdrop = data.get('backdrop', 'white')
                if backdrop not in ['white', 'sky', 'field']:
                    raise ValueError('Invalid backdrop')
                state['backdrop'] = backdrop
                state['size'] = max(10, min(300, self.number(data.get('size', 100), -10000, 10000)))
            elif action == 'go':
                state.update(x=self.number(data['x'], -240, 240), y=self.number(data['y'], -180, 180))
            elif action in ['set_x', 'set_y']:
                axis = action[-1]
                bound = 240 if axis == 'x' else 180
                state[axis] = max(-bound, min(bound, self.number(data[axis], -10000, 10000)))
            elif action == 'bounce':
                limit_x, limit_y = self.edge_limits(state)
                angle = math.radians(state['direction'])
                vx, vy = math.sin(angle), math.cos(angle)
                if (state['x'] >= limit_x and vx > 1e-9) or (state['x'] <= -limit_x and vx < -1e-9):
                    state['direction'] = -state['direction']
                if (state['y'] >= limit_y and vy > 1e-9) or (state['y'] <= -limit_y and vy < -1e-9):
                    state['direction'] = 180 - state['direction']
                state['direction'] %= 360
                state['x'] = max(-limit_x, min(limit_x, state['x']))
                state['y'] = max(-limit_y, min(limit_y, state['y']))
            elif action == 'move':
                steps = self.number(data['steps'], -10000, 10000)
                angle = math.radians(state['direction'])
                state['x'] = max(-240, min(240, state['x'] + math.sin(angle) * steps))
                state['y'] = max(-180, min(180, state['y'] + math.cos(angle) * steps))
            elif action == 'turn':
                state['direction'] = (state['direction'] + self.number(data['degrees'], -36000, 36000)) % 360
            elif action == 'point':
                state['direction'] = self.number(data['direction'], -36000, 36000) % 360
            elif action in ['change_x', 'change_y']:
                axis = action[-1]
                bound = 240 if axis == 'x' else 180
                state[axis] = max(-bound, min(bound, state[axis] + self.number(data['amount'], -10000, 10000)))
            elif action in ['set_size', 'change_size']:
                size = self.number(data['size'], -10000, 10000)
                state['size'] = max(10, min(300, size + (state['size'] if action == 'change_size' else 0)))
            elif action == 'say':
                duration = self.number(data['seconds'], 0, 300) if 'seconds' in data else None
                state['speech'] = str(data.get('text', ''))[:200]
                self.speech_until = time.monotonic() + duration if duration is not None else 0
            elif action in ['show', 'hide']:
                state['visible'] = action == 'show'
            elif action == 'keys':
                keys = data.get('keys', [])
                if not isinstance(keys, list) or any(k not in ['up', 'down', 'left', 'right', 'space'] for k in keys):
                    raise ValueError('Invalid keys')
                self.keys = list(set(keys))
                self.key_time = time.monotonic()
                if 'mouse' in data:
                    mouse = data['mouse']
                    if not isinstance(mouse, dict) or not isinstance(mouse.get('down'), bool):
                        raise ValueError('Invalid mouse input')
                    self.mouse = {'x': self.number(mouse['x'], -240, 240),
                                  'y': self.number(mouse['y'], -180, 180), 'down': mouse['down']}
                    self.mouse_time = time.monotonic()
            else:
                raise ValueError('Unsupported stage action')
            self.state = state
            return self.snapshot()

    def snapshot(self):
        limit_x, limit_y = self.edge_limits(self.state)
        return {**self.state,
                'speech': self.state['speech'] if not self.speech_until or time.monotonic() < self.speech_until else '',
                'keys': self.keys if time.monotonic() - self.key_time < 1 else [],
                'mouse': {**self.mouse, 'down': self.mouse['down'] and time.monotonic() - self.mouse_time < 1},
                'touching_edge': abs(self.state['x']) >= limit_x or abs(self.state['y']) >= limit_y}


def handler(stage):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, data):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path != '/state':
                return self.reply(404, {'ok': False})
            with stage.lock:
                self.reply(200, {'ok': True, 'state': stage.snapshot()})

        def do_POST(self):
            try:
                if self.path != '/command' or self.headers.get('Content-Type') != 'application/json':
                    raise ValueError('JSON command required')
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Object required')
                self.reply(200, {'ok': True, 'state': stage.command(data)})
            except (ValueError, KeyError, TypeError) as error:
                self.reply(400, {'ok': False, 'error': str(error)})
    return Handler


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8092), handler(Stage())).serve_forever()
