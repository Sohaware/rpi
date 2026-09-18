"""Real Linux permission regression checks, run as root in disposable CI only."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("permission_setup", Path(__file__).parents[1] / "installer/app_setup.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@unittest.skipUnless(os.name == "posix" and getattr(os, "geteuid", lambda: -1)() == 0 and shutil.which("setfacl"),
                     "Requires root and ACL tools on a disposable Linux runner")
class WebPermissionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "client"
        self.home.mkdir(mode=0o700)
        for name in ("active_script.py", "log.log"):
            path = self.home / name
            path.write_text("preserve this content\n")
            path.chmod(0o660)
            subprocess.run(["setfacl", "-m", "u:www-data:---", str(path)], check=True)
        for name in ("userfiles", "images", "audio"):
            (self.home / name).mkdir(mode=0o2770)

    def test_denied_access_is_repaired_without_changing_data(self):
        denied = subprocess.run(["runuser", "-u", "www-data", "--", "test", "-w", str(self.home / "active_script.py")])
        self.assertNotEqual(denied.returncode, 0)
        m.repair_web_access(self.home)
        m.repair_web_access(self.home)
        for name in ("active_script.py", "log.log"):
            self.assertEqual((self.home / name).read_text(), "preserve this content\n")

    def test_home_is_not_writable_or_listable_by_web_user(self):
        m.repair_web_access(self.home)
        for access in ("-w", "-r"):
            result = subprocess.run(["runuser", "-u", "www-data", "--", "test", access, str(self.home)])
            self.assertNotEqual(result.returncode, 0)

    def test_new_shared_files_inherit_web_access(self):
        m.repair_web_access(self.home)
        path = self.home / "userfiles" / "student.py"
        path.write_text("print('retained')\n")
        subprocess.run(["runuser", "-u", "www-data", "--", "test", "-w", str(path)], check=True)
