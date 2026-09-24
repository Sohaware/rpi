import hashlib
import importlib.util
import json
import ast
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("app_setup", ROOT / "installer/app_setup.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def release_sha(path):
    if (ROOT / ".git").exists():
        relative = path.relative_to(ROOT).as_posix()
        object_id = subprocess.check_output(
            ["git", "hash-object", "-w", "--path", relative, path],
            cwd=ROOT, text=True,
        ).strip()
        data = subprocess.check_output(
            ["git", "cat-file", "blob", object_id], cwd=ROOT,
        )
    else:
        data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


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

    def test_examples_are_backed_up_then_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            path = base / "CodyNick examples"
            backup = base / "backup"
            path.mkdir()
            (path / "old.py").write_text("student edit")
            m.reset_examples(path, backup)
            self.assertTrue(path.is_dir())
            self.assertEqual(list(path.iterdir()), [])
            relative = Path(*path.parts[1:]) if path.is_absolute() else path
            self.assertEqual((backup / relative / "old.py").read_text(),
                             "student edit")

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

    def test_072_upgrade_is_accepted(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), \
             patch.object(m, "read_json", side_effect=[{"stage": "network-ready"}, {"version": "0.7.2", "stage": "ready"}]), \
             patch.object(m, "run"), patch.object(m.shutil, "disk_usage", return_value=MagicMock(free=4 * 1024 ** 3)):
            m.check_platform()

    def test_074_upgrade_is_accepted(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), \
             patch.object(m, "read_json", side_effect=[{"stage": "network-ready"}, {"version": "0.7.4", "stage": "failed"}]), \
             patch.object(m, "run"), patch.object(m.shutil, "disk_usage", return_value=MagicMock(free=4 * 1024 ** 3)):
            m.check_platform()

    def test_075_upgrade_is_accepted(self):
        with patch.object(m.platform, "freedesktop_os_release", return_value={"ID": "ubuntu", "VERSION_ID": "26.04"}), \
             patch.object(m.platform, "machine", return_value="aarch64"), \
             patch.object(m, "read_json", side_effect=[{"stage": "network-ready"}, {"version": "0.7.5", "stage": "ready"}]), \
             patch.object(m, "run"), patch.object(m.shutil, "disk_usage", return_value=MagicMock(free=4 * 1024 ** 3)):
            m.check_platform()

    def test_ready_clears_stale_failure(self):
        with patch.object(m, "read_json", return_value={"error": "old failure"}), patch.object(m, "write") as write:
            m.save_state("ready")
            self.assertNotIn("error", json.loads(write.call_args.args[1]))

    def test_release_files_and_pins(self):
        manifest = json.loads((ROOT / "releases/core-0.7.6.json").read_text())
        for name, checksum in m.verify_manifest(manifest).items():
            self.assertEqual(release_sha(ROOT / name), checksum, name)
        bootstrap = (ROOT / "bootstrap/codynick-apps.sh").read_text()
        for key, name in (("HELPER", "installer/app_setup.py"), ("MANIFEST", "releases/core-0.7.6.json"), ("VERSION_STATUS", "installer/version_status.py"), ("VISION", "installer/vision_setup.py"), ("SPEECH", "installer/speech_setup.py"), ("OCR", "installer/ocr_setup.py"), ("TTS", "installer/tts_setup.py")):
            pin = re.search(key + r'_SHA256="([0-9a-f]{64})"', bootstrap).group(1)
            self.assertEqual(pin, release_sha(ROOT / name))

    def test_release_sealer_normalizes_git_text(self):
        sealer = (ROOT / "tools/seal_core_release.py").read_text(encoding="utf-8")
        self.assertIn('git", "hash-object", "-w", "--path"', sealer)
        self.assertIn('git", "cat-file", "blob"', sealer)
        entry = (ROOT / "setup.sh").read_text()
        for key, name in (("NETWORK", "bootstrap/codynick-setup.sh"), ("APPS", "bootstrap/codynick-apps.sh")):
            pin = re.search(key + r'_SHA256="([0-9a-f]{64})"', entry).group(1)
            self.assertEqual(pin, release_sha(ROOT / name))

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

    def test_student_script_service_requests_graceful_cleanup(self):
        text = (ROOT / "installer/app_setup.py").read_text()
        self.assertIn("KillMode=control-group", text)
        self.assertIn("KillSignal=SIGINT", text)
        self.assertIn("TimeoutStopSec=10", text)

    def test_offline_docs_and_blockly_assets_are_managed(self):
        manifest = json.loads((ROOT / "releases/core-0.7.6.json").read_text())
        files = manifest["files"]
        self.assertIn("components/ide/docs/docs/01-Start-Here/01-Welcome.md", files)
        self.assertIn("components/ide/docs/assets/gadgets/cjp_neo.png", files)
        self.assertIn("components/ide/teachers/index.php", files)
        self.assertIn("components/ide/teachers/guides/01-temperature-alarm-live-coding.md", files)
        self.assertIn("components/ide/gadget-tests/index.php", files)
        self.assertIn("components/gadget-tests/01-codyjoy-pro.md", files)
        self.assertIn("components/ide/blocks/vendor/blockly/blockly.min.js", files)
        self.assertIn("components/ide/blocks/vendor/blockly/media/sprites.svg", files)
        blockly = (ROOT / "components/ide/blocks/index.php").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("https://unpkg.com", blockly)
        self.assertIn("media: '/blocks/vendor/blockly/media/'", blockly)

    def test_camera_capture_defaults_to_release(self):
        text = (ROOT / "components/ai/codynick_ai/controller.py").read_text()
        self.assertIn("keep_open: bool = False", text)
        self.assertIn("if not keep_open:\n                self.close_camera()", text)

    def test_reference_mentions_every_public_iot_and_ai_method(self):
        docs_root = ROOT / "components/ide/docs/docs"
        docs = "\n".join(path.read_text(encoding="utf-8")
                         for path in docs_root.rglob("*.md"))

        def class_methods(path, class_name):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            target = next(node for node in tree.body
                          if isinstance(node, ast.ClassDef)
                          and node.name == class_name)
            return [node.name for node in target.body
                    if isinstance(node, ast.FunctionDef)
                    and not node.name.startswith("_")
                    and not any(isinstance(item, ast.Name)
                                and item.id == "property"
                                for item in node.decorator_list)]

        public = []
        public += class_methods(
            ROOT / "components/client/Dashboard.py", "Card"
        )
        public += class_methods(
            ROOT / "components/client/CodyNick.py", "WiFi_IoT"
        )
        public += class_methods(
            ROOT / "components/ai/codynick_ai/controller.py", "CodyNickAI"
        )
        public += class_methods(
            ROOT / "components/ai/codynick_ai/controller.py", "SpeechListener"
        )
        public += ["configure", "ensure_database", "ensure_table", "clear"]

        missing = sorted({name for name in public if f"{name}(" not in docs})
        self.assertEqual(missing, [], f"Public methods missing from ODD: {missing}")

    def test_teacher_portal_is_protected_and_password_is_preserved(self):
        text = (ROOT / "installer/app_setup.py").read_text(encoding="utf-8")
        self.assertIn('<Directory /var/www/html/teachers>', text)
        self.assertIn('AuthUserFile /etc/apache2/codynick-teachers.htpasswd', text)
        self.assertIn('if not password_file.exists():', text)
        self.assertIn('"htpasswd", "-bc"', text)
        self.assertIn('teacher_status != "401"', text)

    def test_public_gadget_tests_are_managed_and_copyable(self):
        installer = (ROOT / "installer/app_setup.py").read_text(encoding="utf-8")
        portal = (ROOT / "components/ide/gadget-tests/index.php").read_text(encoding="utf-8")
        self.assertIn('/home/client/CodyNick Gadget Tests', installer)
        self.assertIn('reset_examples(GADGET_TESTS_ROOT, backup)', installer)
        self.assertIn('/gadget-tests/', installer)
        self.assertNotIn('<Directory /var/www/html/gadget-tests>', installer)
        self.assertIn("navigator.clipboard.writeText", portal)
        self.assertEqual(len(list((ROOT / "components/gadget-tests").glob("*.md"))), 11)

    def test_presenter_guide_scope_and_copy_buttons(self):
        guide = (ROOT / "components/ide/teachers/guides/01-temperature-alarm-live-coding.md").read_text(encoding="utf-8")
        portal = (ROOT / "components/ide/teachers/index.php").read_text(encoding="utf-8")
        self.assertIn("# CodyNick Fabric Presenter Guide: Build a CodyNick Temperature Alarm", guide)
        self.assertIn("temperature < 20", guide)
        self.assertIn("range(1, 11)", guide)
        self.assertIn("## Step 9: Connect to AI and Take a Picture", guide)
        self.assertIn('CodyNickAI(workspace="/home/client", camera_index=0)', guide)
        self.assertIn('ai.take_picture("camera_demo")', guide)
        self.assertIn("Images** in the IDE", guide)
        self.assertIn("navigator.clipboard.writeText", portal)

    def test_gadget_library_output_and_rgb_timing(self):
        library = (ROOT / "components/client/CodyNick.py").read_text(encoding="utf-8")
        self.assertIn('class RGB_Matrix:\n    COMMAND_DELAY = 0.005', library)
        self.assertNotIn('log(f"Float = {f}, value trimmed = {value_trimmed}")', library)
        self.assertNotIn('log(f"value in function = {value_trimmed}")', library)

    def test_teacher_guide_uses_the_shipped_gadget_api(self):
        guide = (ROOT / "components/ide/teachers/guides/01-temperature-alarm-live-coding.md").read_text(encoding="utf-8")
        for command in ("CodyNick.CN()", "CodyNick.RGB_Matrix.set(",
                        "CodyNick.Seven_Segment.display(",
                        "CodyNick.Temperature_Sensor.read(",
                        "CodyNick.Joystick.click(",
                        "CodyNick.CJP_Sound_Maker.play_until_done("):
            self.assertIn(command, guide)
        for nonexistent in ("CodyNick.CodyJoy(", "RGB_LED", "SevenSegment(",
                            "CodyNick.Temperature(", ".is_clicked()"):
            self.assertNotIn(nonexistent, guide)

    def test_release_metadata_is_current_and_state_is_readable(self):
        installer = (ROOT / "installer/app_setup.py").read_text(encoding="utf-8")
        homepage = (ROOT / "components/ide/index.php").read_text(encoding="utf-8")
        self.assertIn('write(STATE, json.dumps(data, indent=2) + "\\n", 0o644)', installer)
        self.assertIn('"software_version" => "0.7.6"', homepage)
        self.assertIn('"production_date" => "2026-09-23"', homepage)
        self.assertNotIn("1675-01-01", homepage)


if __name__ == "__main__":
    unittest.main()
