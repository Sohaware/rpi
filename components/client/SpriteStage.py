"""Python bridge for the local Blockly sprite-stage prototype."""
import json
import math
import time
import urllib.request


class SpriteStage:
    def __init__(self, **settings):
        self._command('begin', **settings)

    def _command(self, action, **values):
        request = urllib.request.Request('http://127.0.0.1:8092/command',
            data=json.dumps(dict(action=action, **values)).encode(),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=3) as response:
            result = json.load(response)
        if not result.get('ok'):
            raise RuntimeError(result.get('error', 'Stage request failed'))
        return result['state']

    def move(self, steps):
        self._command('move', steps=steps)

    def turn(self, degrees):
        self._command('turn', degrees=degrees)

    def point_direction(self, direction):
        self._command('point', direction=direction)

    def change_x(self, amount):
        self._command('change_x', amount=amount)

    def change_y(self, amount):
        self._command('change_y', amount=amount)

    def set_size(self, size):
        self._command('set_size', size=size)

    def change_size(self, size):
        self._command('change_size', size=size)

    def go(self, x, y):
        self._command('go', x=x, y=y)

    def set_x(self, x):
        self._command('set_x', x=x)

    def set_y(self, y):
        self._command('set_y', y=y)

    def glide(self, seconds, x, y):
        seconds, x, y = float(seconds), float(x), float(y)
        if not all(math.isfinite(value) for value in [seconds, x, y]) or not 0 <= seconds <= 300 or not -240 <= x <= 240 or not -180 <= y <= 180:
            raise ValueError('Glide requires 0..300 seconds and coordinates inside the stage.')
        initial = self._state()
        start = time.monotonic()
        while True:
            progress = min(1, (time.monotonic() - start) / seconds) if seconds else 1
            self.go(initial['x'] + (x - initial['x']) * progress, initial['y'] + (y - initial['y']) * progress)
            if progress >= 1:
                return
            time.sleep(min(0.05, max(0, seconds - (time.monotonic() - start))))

    def bounce(self):
        self._command('bounce')

    def say(self, text):
        self._command('say', text=str(text))

    def say_for(self, text, seconds):
        seconds = float(seconds)
        if not math.isfinite(seconds) or not 0 <= seconds <= 300:
            raise ValueError('Speech duration must be 0..300 seconds.')
        self._command('say', text=str(text), seconds=seconds)
        time.sleep(seconds)

    def show(self):
        self._command('show')

    def hide(self):
        self._command('hide')

    def _state(self):
        with urllib.request.urlopen('http://127.0.0.1:8092/state', timeout=3) as response:
            return json.load(response)['state']

    def x(self):
        return self._state()['x']

    def y(self):
        return self._state()['y']

    def direction(self):
        return (self._state()['direction'] + 180) % 360 - 180

    def size(self):
        return self._state()['size']

    def key_pressed(self, key):
        return key in self._state()['keys']

    def mouse_x(self):
        return self._state()['mouse']['x']

    def mouse_y(self):
        return self._state()['mouse']['y']

    def mouse_down(self):
        return self._state()['mouse']['down']

    def go_to_mouse(self):
        mouse = self._state()['mouse']
        self.go(mouse['x'], mouse['y'])

    def touching_edge(self):
        return self._state()['touching_edge']
