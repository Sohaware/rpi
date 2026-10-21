import importlib.util
from pathlib import Path
import sys
import struct
import unittest
from unittest.mock import MagicMock, mock_open, patch


class ScriptControlTests(unittest.TestCase):
    def test_release_installs_socket_and_disables_it_for_older_targets(self):
        spec = importlib.util.spec_from_file_location('control_installer', Path(__file__).parents[1] / 'installer/app_setup.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for components, enabled in [({'script-control': 'socket-1'}, True), ({}, False)]:
            with patch.object(installer, 'run') as run, patch.object(installer, 'deploy') as deploy, \
                 patch.object(Path, 'exists', return_value=False), patch.object(Path, 'unlink'):
                installer.configure_script_control({'components': components}, Path('/backup'))
                if enabled:
                    self.assertEqual(deploy.call_count, 2)
                    run.assert_any_call('systemctl', 'enable', '--now', 'codynick-script-control.socket')
                else:
                    deploy.assert_not_called()
                    run.assert_any_call('systemctl', 'disable', 'codynick-script-control.socket', check=False)

    def load(self):
        spec = importlib.util.spec_from_file_location('script_control', Path(__file__).parents[1] / 'components/watchdog/script_control.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'fcntl': MagicMock()}):
            spec.loader.exec_module(module)
        return module

    def test_stop_marks_before_stopping_only_student_service(self):
        module = self.load()
        events = []
        with patch.object(module.os, 'geteuid', return_value=0, create=True), \
             patch.object(sys, 'argv', ['control', 'stop']), \
             patch('builtins.open', mock_open()), \
             patch.object(module, 'STOPPED') as marker, \
             patch.object(module.subprocess, 'run') as run:
            marker.touch.side_effect = lambda **kw: events.append('marker')
            run.side_effect = lambda *a, **kw: events.append('stop')
            module.main()
            self.assertEqual(events, ['marker', 'stop'])
            run.assert_called_once_with(['systemctl', 'stop', 'script.service'], check=True, timeout=20)

    def test_unrecognized_action_is_rejected(self):
        module = self.load()
        with patch.object(module.os, 'geteuid', return_value=0, create=True), patch.object(sys, 'argv', ['control', 'shell']):
            with self.assertRaises(SystemExit):
                module.main()

    def test_start_restarts_even_with_unchanged_source(self):
        module = self.load()
        with patch.object(module.os, 'geteuid', return_value=0, create=True), \
             patch.object(sys, 'argv', ['control', 'start']), \
             patch('builtins.open', mock_open(read_data=b'print(1)')), \
             patch.object(module, 'STOPPED') as marker, \
             patch.object(module, 'Path') as path, patch.object(module.subprocess, 'run') as run:
            module.main()
            marker.unlink.assert_called_once_with(missing_ok=True)
            run.assert_called_once_with(['systemctl', 'restart', 'script.service'], check=True, timeout=20)
            path.return_value.write_text.assert_called_once()

    def test_socket_allows_only_fixed_actions_and_authorized_peer(self):
        module = self.load()
        for uid, request, expected in [(33, b'stop\n', True), (33, b'start\n', True),
                                       (1000, b'stop\n', False), (33, b'shell\n', False)]:
            client = MagicMock()
            client.getsockopt.return_value = struct.pack('3i', 123, uid, 33)
            client.recv.return_value = request
            with patch.object(module.socket, 'SO_PEERCRED', 17, create=True), patch.object(module, 'control') as control:
                module.handle_client(client, {0, 33})
                self.assertEqual(control.called, expected)
                response = module.json.loads(client.sendall.call_args.args[0])
                self.assertEqual(response['ok'], expected)
