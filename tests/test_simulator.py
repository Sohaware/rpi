import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import tempfile
import types
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

with patch.object(sys, 'path', [str(Path(__file__).resolve().parents[1] / 'components/simulator'), str(Path(__file__).resolve().parents[1] / 'components/client'), *sys.path]):
    from server import State, handler, display_number
    from CodyNickSimulator import Simulator
    from wifi_sim import WiFiModel

ROOT = Path(__file__).resolve().parents[1]
TOKEN = 'a' * 64


class SimulatorTests(unittest.TestCase):
    def test_soil_percentage_bounds_and_legacy_scene(self):
        scene = {'gadgets': {'cjp': {'x': 40, 'y': 40}}, 'soil': 100}
        self.assertEqual(State.validate_scene(scene)['soil'], 100)
        for value in [-1, 101]:
            with self.assertRaises(ValueError):
                State.validate_scene({**scene, 'soil': value})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'scene.json'
            path.write_text(json.dumps({**scene, 'soil': 500}))
            restored = State(path)
            self.assertEqual(restored.scene['soil'], 100)
            self.assertEqual(restored.scene['gadgets'], scene['gadgets'])

    @classmethod
    def setUpClass(cls):
        cls.state = State()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler(TOKEN, cls.state))
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def setUp(self):
        self.state.session = None
        self.state.leds = ['#000000'] * 16
        self.state.scene = {'gadgets': {kind: {'x': 40, 'y': 40} for kind in ['cjp', 'seven', 'temperature', 'matrix', 'joystick', 'ultrasonic', 'soil', 'wifi']}, 'temperature': 21.1}
        self.state.wifi = WiFiModel()

    def request(self, path, body=None, authenticated=True):
        headers = {'Authorization': 'Bearer ' + TOKEN} if authenticated else {}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.url + path, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        return urllib.request.urlopen(request, timeout=2)

    def test_auth_and_path_restriction(self):
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/state', authenticated=False)
        self.assertEqual(exc.exception.code, 401)
        with self.request('/?token=' + TOKEN, authenticated=False) as reply:
            self.assertIn('HttpOnly', reply.headers['Set-Cookie'])
            self.assertIn(b'CodyJoy Pro', reply.read())
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/../server.py')
        self.assertEqual(exc.exception.code, 404)

    def test_real_gadget_api_over_simulated_transport(self):
        # Import the unmodified production API with external hardware deps stubbed.
        serial = types.ModuleType('serial')
        tools = types.ModuleType('serial.tools')
        ports = types.ModuleType('serial.tools.list_ports')
        ports.comports = lambda: self.fail('Simulator attempted physical port discovery')
        tools.list_ports = ports
        serial.tools = tools
        stubs = {'keyboard': types.ModuleType('keyboard'), 'serial': serial,
                 'serial.tools': tools, 'serial.tools.list_ports': ports,
                 'requests': types.ModuleType('requests')}
        source = ROOT / 'components/client/CodyNick.py'
        spec = importlib.util.spec_from_file_location('hardware_api_test', source)
        api = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, stubs):
            spec.loader.exec_module(api)
        with patch.dict(os.environ, {'CODYNICK_SIM_URL': self.url}), patch.object(Path, 'read_text', return_value=TOKEN):
            cody = Simulator()
        try:
            api.RGB_Matrix.set(cody, 15, '#00FF00')
            self.assertEqual(self.state.leds[15], '#00FF00')
            api.RGB_Matrix.set_xy(cody, 0, 0, 0)
            self.assertEqual(self.state.leds[0], '#FF0000')
            api.RGB_Matrix.set(cody, 1, [100, 0, 100])
            self.assertEqual(self.state.leds[1], '#FF00FF')
            self.state.command({'action': 'input', 'states': ['UP', 'CLICK']})
            self.assertEqual(api.Joystick.states(cody, 'CJP'), ['UP', 'CLICK'])
            self.assertTrue(api.Joystick.position(cody, 'CJP', 'up'))
            self.assertTrue(api.Joystick.click(cody, 5))
            api.CJP_Sound_Maker.play(cody, 'C7', 150)
            self.assertEqual(self.state.notes[-1]['frequency'], 2093)
            api.RGB_Matrix.clear(cody)
            self.assertEqual(self.state.leds, ['#000000'] * 16)
            for value, expected in [(25, '25'), (21.1, '21.1'), (-5, '-5'), (0, '0'), (9999, '9999'), (10000, '----'), (-1000, '----')]:
                api.Seven_Segment.display(cody, 'Stand-Alone', value)
                self.assertEqual(self.state.snapshot()['seven_segment'], expected)
            api.Seven_Segment.display(cody, 0, 10)
            self.assertEqual(api.Temperature_Sensor.read(cody), 21.1)
            self.state.scene['temperature'] = -12.3
            self.assertEqual(api.Temperature_Sensor.read(cody), -12.3)
            api.LED_Matrix.display_text(cody, 'Hello!', 'fast')
            self.assertEqual(self.state.matrix['text'], 'Hello!')
            self.assertEqual(self.state.matrix['speed'], 2)
            api.LED_Matrix.on(cody, 2, 3)
            self.assertEqual(self.state.matrix['mode'], 'pixels')
            self.assertEqual(self.state.matrix['pixels'][26], 1)
            api.LED_Matrix.off(cody, 2, 3)
            self.assertEqual(self.state.matrix['pixels'][26], 0)
            api.LED_Matrix.clear(cody)
            self.assertEqual(self.state.matrix['pixels'], [0] * 64)
            self.state.command({'action': 'input', 'device': 'joystick', 'states': ['DOWN', 'CLICK']})
            self.assertEqual(api.Joystick.states(cody, 'Stand-Alone'), ['DOWN', 'CLICK'])
            self.assertEqual(api.Joystick.states(cody, 'CJP'), ['UP', 'CLICK'])
            self.assertEqual(api.Ultrasonic_Sensor.read(cody, 'Stand-Alone'), 50)
            self.assertEqual(api.Soil_Moisture_Sensor.read(cody), 50)
            self.state.scene.update(distance=12.3, soil=73)
            self.assertEqual(api.Ultrasonic_Sensor.read(cody, 0), 12.3)
            self.assertEqual(api.Soil_Moisture_Sensor.read(cody), 73)
            api.WiFi_IoT.IOT_WRITE_DELAY_SECONDS = 0
            self.assertEqual(api.WiFi_IoT.status(cody), {'wifi': 0, 'iot': 0})
            self.assertTrue(api.WiFi_IoT.set_wifi(cody, 'demo-network', 'demo-only'))
            self.assertTrue(api.WiFi_IoT.set_iot(cody, 'demo-user', 'demo-device', 'demo-key'))
            self.assertEqual(api.WiFi_IoT.status(cody), {'wifi': 3, 'iot': 1})
            self.assertTrue(api.WiFi_IoT.keep_alive_wifi(cody, 'demo-network', 'demo-only'))
            self.assertTrue(api.WiFi_IoT.keep_alive_iot(cody, 'demo-user', 'demo-device', 'demo-key'))
            for kind, value, expected in [('int', 42, 42), ('float', 21.1, 21.1), ('bool', True, True), ('string', 'Hello!', 'Hello!')]:
                self.assertTrue(getattr(api.WiFi_IoT, 'write_' + kind)(cody, 0, value))
                self.assertEqual(getattr(api.WiFi_IoT, 'read_' + kind)(cody, 0), expected)
            self.assertEqual(api.WiFi_IoT.get_wifi_ssid(cody), 'demo-network')
            self.assertEqual(api.WiFi_IoT.get_wifi_password(cody), 'demo-only')
            self.assertEqual(api.WiFi_IoT.get_device_id(cody), 'demo-device')
            self.assertEqual(api.WiFi_IoT.get_device_key(cody), 'demo-key')
            self.assertEqual(api.WiFi_IoT.get_username(cody), 'demo-user')
            self.assertEqual(api.WiFi_IoT.get_esp_version(cody), 'sim-esp')
            self.assertTrue(api.WiFi_IoT.restart(cody))
            self.assertTrue(api.WiFi_IoT.reset_wifi(cody))
            self.assertTrue(api.WiFi_IoT.reset_iot(cody))
            self.state.scene['wifi_link'] = False
            self.assertFalse(api.WiFi_IoT.wifi_connected(cody))
            self.assertFalse(api.WiFi_IoT.iot_connected(cody))
            self.assertFalse(api.WiFi_IoT.write_int(cody, 0, 100))
            self.assertIsNone(api.WiFi_IoT.read_int(cody, 0))
            self.assertNotIn('demo-only', json.dumps(self.state.snapshot()['wifi']))
            with self.assertRaises(ValueError):
                self.state.command({'action': 'open'})
        finally:
            cody.close()
        self.assertFalse(self.state.snapshot()['connected'])
        self.assertEqual(self.state.snapshot()['seven_segment'], '10')

    def test_four_digit_formatting(self):
        for raw, expected in [('25.0', '25'), ('21.1', '21.1'), ('-5.0', '-5'), ('-12.34', '-12.3'),
                              ('9999', '9999'), ('10000', '----'), ('nan', '----'), ('0.125', '0.125')]:
            self.assertEqual(display_number(raw), expected)

    def test_missing_gadget_reports_error(self):
        del self.state.scene['gadgets']['seven']
        session = self.state.command({'action': 'open'})['session']
        with self.assertRaisesRegex(ValueError, 'Add Seven-segment display'):
            self.state.command({'action': 'seven_segment', 'session': session, 'device': 0, 'value': '25'})
        self.assertIn('Add Seven-segment', self.state.snapshot()['error'])

    def test_layout_and_sensor_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scene.json'
            original = State(path)
            original.save_scene(self.state.scene)
            original.scene['temperature'] = 35.2
            original.scene['gadgets']['seven'] = {'x': 440, 'y': 88}
            original.save_scene(original.scene)
            restarted = State(path)
            self.assertEqual(restarted.scene['temperature'], 35.2)
            self.assertEqual(restarted.scene['gadgets']['seven'], {'x': 440, 'y': 88})
            self.assertEqual(len(restarted.scene['gadgets']), 8)

    def test_live_sensor_change_and_fixed_hardware_set(self):
        session = self.state.command({'action': 'open'})['session']
        updated = json.loads(json.dumps(self.state.scene))
        updated['temperature'] = 30.5
        self.state.command({'action': 'scene', 'scene': updated})
        self.assertEqual(self.state.command({'action': 'temperature', 'session': session})['temperature'], 30.5)
        del updated['gadgets']['matrix']
        with self.assertRaisesRegex(ValueError, 'Stop the Python'):
            self.state.command({'action': 'scene', 'scene': updated})
        for temperature in [float('nan'), 126, -56]:
            with self.assertRaises(ValueError):
                self.state.save_scene({'gadgets': {'cjp': {'x': 0, 'y': 0}}, 'temperature': temperature})

    def test_stale_inputs_and_crashed_script_reset(self):
        self.state.command({'action': 'open'})
        self.state.command({'action': 'input', 'states': ['LEFT']})
        self.state.input_seen -= 2
        self.assertEqual(self.state.snapshot()['states'], [])
        self.state.leds[0] = '#FF0000'
        self.state.seen -= 4
        self.assertFalse(self.state.snapshot()['connected'])
        self.assertEqual(self.state.leds[0], '#000000')

    def test_invalid_requests(self):
        session = self.state.command({'action': 'open'})['session']
        for payload in [dict(action='led', index=16, color='#FFFFFF', session=session),
                        dict(action='led', index=0, color='invalid', session=session),
                        dict(action='input', states=['INVALID']),
                        dict(action='heartbeat', session='wrong')]:
            with self.assertRaises(urllib.error.HTTPError) as exc:
                self.request('/command', payload)
            self.assertEqual(exc.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
