import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('network_setup', Path(__file__).parents[1] / 'bootstrap/network_setup.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class NetworkTests(unittest.TestCase):
    def test_dynamic_interfaces(self):
        records = [dict(name='wlan0', wifi=True, usb=False, physical=True),
                   dict(name='wlxOTHER', wifi=True, usb=True, physical=True),
                   dict(name='eth0', wifi=False, usb=False, physical=True),
                   dict(name='lo', wifi=False, usb=False, physical=False)]
        self.assertEqual(m.choose_interfaces(records), ('wlan0', ['wlxOTHER'], ['eth0']))

    def test_multiple_usb_requires_selection(self):
        records = [dict(name='wlan0', wifi=True, usb=False, physical=True)]
        records += [dict(name=n, wifi=True, usb=True, physical=True) for n in ['wlan1', 'wlan2']]
        with self.assertRaises(RuntimeError): m.choose_interfaces(records)

    def test_wifi_removal_preserves_other_networks(self):
        doc = {'network': {'version': 2, 'ethernets': {'eth0': {'dhcp4': True}},
                           'wifis': {'wlan0': {'access-points': {'private': {}}},
                                     'wlxOTHER': m.dongle_config('AE')}}}
        new = m.remove_wifi(doc, ['wlan0'])
        self.assertIn('wlan0', doc['network']['wifis'])
        self.assertNotIn('wlan0', new['network']['wifis'])
        self.assertEqual(new['network']['ethernets'], doc['network']['ethernets'])
        self.assertEqual(new['network']['wifis']['wlxOTHER'], doc['network']['wifis']['wlxOTHER'])

    def test_no_unsupported_networkd_match(self):
        cfg = m.dongle_config('AE')
        self.assertNotIn('match', cfg)
        self.assertEqual(cfg['dhcp4-overrides']['route-metric'], 700)
        self.assertEqual(cfg['access-points']['codynick']['password'], 'codynick')

    def test_probe_binds_to_specific_device(self):
        with patch.object(m, 'run') as run:
            run.return_value.returncode = 0
            self.assertTrue(m.internet('wlx123'))
            args = run.call_args.args
            self.assertEqual(args[args.index('--interface') + 1], 'wlx123')
            self.assertIn('--fail', args)
            run.return_value.returncode = 7
            self.assertFalse(m.internet('wlx123'))

    def test_failed_services_cannot_confirm(self):
        with patch.object(m, 'load', return_value={'stage': 'applying'}), \
             patch.object(m, 'active', return_value=False), patch.object(m, 'save') as save:
            with self.assertRaises(RuntimeError): m.confirm()
            save.assert_not_called()

    def test_confirm_requires_internet(self):
        state = dict(stage='applying', uplinks=['wlx123'])
        with patch.object(m, 'load', return_value=state), patch.object(m, 'active', return_value=True), \
             patch.dict(m.os.environ, {'SSH_CONNECTION': ''}), patch('builtins.input', return_value='y'), \
             patch.object(m, 'internet', return_value=False), patch.object(m, 'save') as save:
            with self.assertRaises(RuntimeError): m.confirm()
            save.assert_not_called()

    def test_confirm_wrong_ssh_address(self):
        with patch.object(m, 'load', return_value={'stage': 'applying'}), \
             patch.object(m, 'active', return_value=True), \
             patch.dict(m.os.environ, {'SSH_CONNECTION': '10.1.1.9 2222 10.1.1.2 22'}):
            with self.assertRaises(RuntimeError): m.confirm()

    def test_snapshot_keeps_original(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'config.yaml'
            p.write_text('original')
            state = dict(files={}, backup=str(Path(d) / 'backup'))
            # Linux absolute paths are used on device; use a relative test path on Windows.
            with patch.object(m, 'save'), patch.object(m.shutil, 'copy2') as cp:
                m.snapshot(state, p)
                p.write_text('changed')
                m.snapshot(state, p)
                self.assertEqual(cp.call_count, 1)

    def test_rollback_does_nothing_after_confirmation(self):
        with patch.object(m, 'load', return_value={'stage': 'network-ready'}), patch.object(m, 'run') as run:
            m.rollback()
            run.assert_not_called()

    def test_confirmation_records_success_and_disarms_timer(self):
        state = dict(stage='applying', uplinks=['eth0'])
        with patch.object(m, 'load', return_value=state), patch.object(m, 'active', return_value=True), \
             patch.dict(m.os.environ, {'SSH_CONNECTION': '10.42.0.50 1234 10.42.0.1 22'}), \
             patch('builtins.input', return_value='y'), patch.object(m, 'internet', return_value=True), \
             patch.object(m, 'save') as save, patch.object(m, 'run') as run, patch.object(m, 'show'):
            m.confirm()
            self.assertEqual(save.call_args.args[0]['stage'], 'network-ready')
            run.assert_called_once_with('systemctl', 'disable', '--now', 'codynick-rollback.timer')

    def test_handover_failure_restores_previous_configuration(self):
        state = dict(stage='pending', ap='wlan0')
        with patch.object(m, 'load', return_value=state), patch.object(m, 'save'), \
             patch.object(m, 'configs', return_value={}), patch.object(m, 'managed_write'), \
             patch.object(m, 'run', side_effect=RuntimeError('netplan failed')), \
             patch.object(m, 'rollback') as rollback:
            with self.assertRaisesRegex(RuntimeError, 'netplan failed'): m.apply_handover()
            rollback.assert_called_once()

    def test_configuration_keeps_existing_firewall(self):
        state = dict(ap='wlan0', wired=['eth0'], usb=['wlx123'], ssid='codynick-12345678', country='AE')
        files = {}
        with patch.object(m, 'managed_write', side_effect=lambda s,p,t,*a: files.update({str(p):t})), \
             patch.object(m, 'write'), patch.object(m, 'run'):
            m.configure_services(state)
        nat = next(text for name,text in files.items() if name.endswith('nat.nft'))
        self.assertNotIn('flush ruleset', nat)
        self.assertIn('"eth0", "wlx123"', nat)
        cfg = m.yaml_module().safe_load(files['/etc/netplan/95-codynick-route-priority.yaml'])
        self.assertEqual(cfg['network']['ethernets']['eth0']['dhcp4-overrides']['route-metric'], 100)
        self.assertEqual(cfg['network']['wifis']['wlx123']['dhcp4-overrides']['route-metric'], 200)

if __name__ == '__main__': unittest.main()
