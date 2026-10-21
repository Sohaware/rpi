import importlib.util
import hashlib
import json
from pathlib import Path
import re
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('selection_installer', 'installer/app_setup.py')
selector = load('release_selector', 'tools/select_release.py')


class ReleaseSelectionTests(unittest.TestCase):
    def test_default_target_manifest_is_pinned(self):
        entry = (ROOT / 'setup.sh').read_text()
        version = re.search(r'^TARGET_VERSION="([^"]+)"', entry, re.M).group(1)
        digest = re.search(r'^TARGET_MANIFEST_SHA256="([^"]+)"', entry, re.M).group(1)
        data = (ROOT / f'releases/core-{version}.json').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), digest)

    def test_original_three_previous_releases_can_be_selected_from_current_install(self):
        for version in ['0.9.10', '0.9.9', '0.9.8']:
            manifest = json.loads((ROOT / f'releases/core-{version}.json').read_text())
            with patch.multiple(installer, VERSION='0.10.0', TAG=installer.ENGINE_TAG,
                                RELEASE_DATE='2026-10-20', BASE='unused'):
                installer.select_target(manifest)
                self.assertEqual(installer.VERSION, version)
                self.assertEqual(installer.TAG, manifest['tag'])
                self.assertEqual(installer.BASE, f"https://raw.githubusercontent.com/Sohaware/rpi/{manifest['tag']}/")
                installer.verify_manifest(manifest)
                self.assertNotIn('simulator', manifest['components'])
                with patch.object(installer.platform, 'freedesktop_os_release', return_value={'ID':'ubuntu','VERSION_ID':'26.04'}), \
                     patch.object(installer.platform, 'machine', return_value='aarch64'), \
                     patch.object(installer, 'read_json', side_effect=[{'stage':'network-ready'}, {'version':'0.10.0'}]), \
                     patch.object(installer, 'run'), \
                     patch.object(installer.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=4 * 1024**3)):
                    installer.check_platform()
                self.assertEqual(selector.published_manifest(version)[0], manifest['tag'])

    def test_wrong_tag_is_rejected_before_deployment(self):
        with self.assertRaises(RuntimeError):
            installer.select_target({'version': '0.9.10', 'tag': 'main'})

    def test_maintainer_selector_keeps_updater_and_network_pins(self):
        original = (ROOT / 'setup.sh').read_text()
        tag, checksum = selector.published_manifest('0.9.10')
        updated = selector.render_selector(original, '0.9.10', tag, checksum)
        self.assertIn('TARGET_VERSION="0.9.10"', updated)
        self.assertIn('TARGET_TAG="v0.9.10-temperature-nan"', updated)
        for name in ['VERSION', 'NETWORK_SHA256', 'APPS_SHA256']:
            pattern = '^' + name + '="[^"]+"'
            self.assertEqual(re.search(pattern, original, re.M).group(), re.search(pattern, updated, re.M).group())

    def test_downgrade_disables_simulator_without_resetting_layout(self):
        manifest = {'components': {}}
        with patch.object(Path, 'exists', return_value=True), patch.object(installer, 'run') as run:
            installer.configure_simulator(manifest)
        run.assert_called_once_with('systemctl', 'disable', '--now', 'codynick-simulator')

    def test_pc_is_still_rejected(self):
        with patch.object(installer.platform, 'freedesktop_os_release', return_value={'ID':'ubuntu','VERSION_ID':'26.04'}), patch.object(installer.platform, 'machine', return_value='x86_64'):
            with self.assertRaisesRegex(RuntimeError, 'ARM64'):
                installer.check_platform()
