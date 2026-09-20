import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("app_setup", ROOT / "installer/app_setup.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AppTests(unittest.TestCase):
    def manifest(self, name="components/client/CodyNick.py", digest="a" * 64):
        return dict(version=m.VERSION, tag=m.TAG, files={name: digest})

    def test_manifest_rejects_traversal_and_wrong_components(self):
        for name in ("/etc/passwd", "components/../passwd", "components", "components/unknown/model", "components\\client\\bad"):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                m.verify_manifest(self.manifest(name))

    def test_manifest_rejects_wrong_version_and_checksum(self):
        with self.assertRaises(RuntimeError):
            m.verify_manifest(dict(self.manifest(), version="9.0"))
        with self.assertRaises(RuntimeError):
            m.verify_manifest(self.manifest(digest="not a checksum"))

    def test_checksum_rejects_download_without_writing(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"wrong content"
        with tempfile.TemporaryDirectory() as temp, patch.object(m.urllib.request, "urlopen", return_value=response):
            with self.assertRaises(RuntimeError):
                m.download_sources(self.manifest(), Path(temp))
            self.assertFalse((Path(temp) / "components/client/CodyNick.py").exists())

    def test_valid_download_and_cache(self):
        response = MagicMock()
        data = b"test data"
        response.__enter__.return_value.read.return_value = data
        manifest = self.manifest(digest=hashlib.sha256(data).hexdigest())
        with tempfile.TemporaryDirectory() as temp, patch.object(m.urllib.request, "urlopen", return_value=response) as fetch:
            m.download_sources(manifest, Path(temp))
            m.download_sources(manifest, Path(temp))
            self.assertEqual(fetch.call_count, 1)

    def test_preserved_file_is_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            src, dst = base / "src", base / "dst"
            src.write_text("new default")
            dst.write_text("student data")
            m.deploy(src, dst, base / "backup", preserve=True)
            self.assertEqual(dst.read_text(), "student data")

    def test_new_preserved_default_is_installed(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            src, dst = base / "src", base / "dst"
            src.write_text("default")
            m.deploy(src, dst, base / "backup", preserve=True)
            self.assertEqual(dst.read_text(), "default")

    def test_symlink_destination_is_rejected(self):
        with patch.object(Path, "is_symlink", return_value=True), self.assertRaises(RuntimeError):
            m.safe_destination(Path("/home/client/CodyNick.py"))

    def test_child_process_umask(self):
        with patch.object(m.subprocess, "run") as child:
            m.run("example")
            self.assertEqual(child.call_args.kwargs["umask"], 0o022)

    def test_access_probe_uses_real_io_not_external_test(self):
        with patch.object(m, "run") as run:
            m.check_web_access()
            args = run.call_args.args
            self.assertIn("/usr/bin/python3", args)
            self.assertNotIn("test", args)
            self.assertIn("os.O_RDWR", args[6])
            self.assertNotIn("O_TRUNC", args[6])

    def test_legacy_install_is_rejected(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), \
             patch.object(m, "read_json", side_effect=[{"stage": "network-ready"}, {}]), \
             patch.object(m, "run"), patch.object(Path, "exists", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "legacy"):
                m.check_platform()

    def test_network_ready_required(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), patch.object(m, "read_json", return_value={"stage": "preparing"}):
            with self.assertRaisesRegex(RuntimeError, "confirm"):
                m.check_platform()

    def test_failed_020_is_accepted_for_repair(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), \
             patch.object(m, "read_json", side_effect=[{"stage": "network-ready"}, {"version": "0.2.0", "stage": "failed"}]), \
             patch.object(m, "run"), patch.object(m.shutil, "disk_usage", return_value=MagicMock(free=4 * 1024 ** 3)):
            m.check_platform()

    def test_unknown_release_is_rejected(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), \
             patch.object(m, "read_json", side_effect=[{"stage": "network-ready"}, {"version": "9.0"}]), patch.object(m, "run"):
            with self.assertRaisesRegex(RuntimeError, "cannot migrate"):
                m.check_platform()

    def test_030_upgrade_is_accepted(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), \
             patch.object(m, "read_json", side_effect=[{"stage": "network-ready"}, {"version": "0.3.0", "stage": "ready"}]), \
             patch.object(m, "run"), patch.object(m.shutil, "disk_usage", return_value=MagicMock(free=4 * 1024 ** 3)):
            m.check_platform()

    def test_ready_clears_stale_failure(self):
        with patch.object(m, "read_json", return_value={"error": "old failure"}), patch.object(m, "write") as write:
            m.save_state("ready")
            self.assertNotIn("error", json.loads(write.call_args.args[1]))

    def test_release_files_and_pins(self):
        manifest = json.loads((ROOT / "releases/core-0.5.1.json").read_text())
        for name, checksum in m.verify_manifest(manifest).items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), checksum, name)
        bootstrap = (ROOT / "bootstrap/codynick-apps.sh").read_text()
        for key, name in (("HELPER", "installer/app_setup.py"), ("MANIFEST", "releases/core-0.5.1.json"), ("VISION", "installer/vision_setup.py"), ("SPEECH", "installer/speech_setup.py"), ("OCR", "installer/ocr_setup.py")):
            pin = re.search(key + r'_SHA256="([0-9a-f]{64})"', bootstrap).group(1)
            self.assertEqual(pin, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
        entry = (ROOT / "setup.sh").read_text()
        for key, name in (("NETWORK", "bootstrap/codynick-setup.sh"), ("APPS", "bootstrap/codynick-apps.sh")):
            pin = re.search(key + r'_SHA256="([0-9a-f]{64})"', entry).group(1)
            self.assertEqual(pin, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())

    def test_no_network_configuration_commands(self):
        text = (ROOT / "installer/app_setup.py").read_text()
        for forbidden in ('"netplan"', '"dnsmasq"', '"reboot"', '"nft"', '"NetworkManager"'):
            self.assertNotIn(forbidden, text)

    def test_apache_root_prefers_php_and_rejects_default_page(self):
        text = (ROOT / "installer/app_setup.py").read_text()
        self.assertIn("DirectoryIndex disabled", text)
        self.assertIn("DirectoryIndex index.php index.html", text)
        self.assertIn("Apache2 Default Page", text)

    def test_block_output_uses_installed_active_script(self):
        text = (ROOT / "components/ide/blocks/index.php").read_text(encoding="utf-8")
        self.assertIn("$PYTHON_OUTPUT_FILE = '/home/client/active_script.py';", text)
        self.assertIn("'# CodyNick run: '", text)


if __name__ == "__main__":
    unittest.main()
