"""Exercise actual PHP endpoints using temporary student data, never a real Pi home."""
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("php"), "PHP is required for HTTP integration checks")
class IdeHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.web = self.base / "web"
        shutil.copytree(ROOT / "components/ide", self.web)
        self.home = self.base / "client"
        (self.home / "userfiles").mkdir(parents=True)
        (self.home / "active_script.py").write_text("# original\n")
        (self.home / "log.log").write_text("")
        for relative in ("code/config.php", "blocks/index.php"):
            path = self.web / relative
            path.write_text(path.read_text(encoding="utf-8").replace("/home/client", self.home.as_posix()), encoding="utf-8")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        self.server = subprocess.Popen(["php", "-S", f"127.0.0.1:{port}", "-t", str(self.web)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop_server)
        for _ in range(100):
            try:
                urllib.request.urlopen(self.url + "/code/", timeout=1).close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            self.fail("PHP test server did not start")

    def stop_server(self):
        self.server.terminate()
        self.server.wait(timeout=10)

    def request(self, path, data=None, json_body=False):
        headers = {}
        if data is not None:
            if json_body:
                data = json.dumps(data).encode()
                headers["Content-Type"] = "application/json"
            else:
                data = urllib.parse.urlencode(data).encode()
        with urllib.request.urlopen(urllib.request.Request(self.url + path, data=data, headers=headers), timeout=10) as response:
            return json.load(response)

    def test_run_twice_changes_watchdog_input(self):
        args = {"action": "run", "content": "print('hello')\n"}
        self.assertTrue(self.request("/code/", args)["ok"])
        first = (self.home / "active_script.py").read_text()
        self.assertTrue(self.request("/code/", args)["ok"])
        second = (self.home / "active_script.py").read_text()
        self.assertNotEqual(first, second)
        self.assertIn("print('hello')", second)

    def test_log_offset_reads_new_output(self):
        log = self.home / "log.log"
        log.write_text("first\n")
        first = self.request("/code/?action=logs&offset=0")
        with log.open("a") as handle:
            handle.write("second\n")
        second = self.request("/code/?action=logs&offset=" + str(first["offset"]))
        self.assertEqual(first["content"], "first\n")
        self.assertEqual(second["content"], "second\n")

    def test_blockly_runs_without_home_directory_write_permission(self):
        if __import__("os").name != "posix":
            self.skipTest("POSIX directory permissions required")
        self.home.chmod(0o555)
        self.addCleanup(self.home.chmod, 0o755)
        args = {"python": "print('blocks')", "workspace": {}}
        self.assertTrue(self.request("/blocks/?api=run", args, json_body=True)["ok"])
        first = (self.home / "active_script.py").read_text()
        self.assertTrue(self.request("/blocks/?api=run", args, json_body=True)["ok"])
        self.assertNotEqual(first, (self.home / "active_script.py").read_text())


if __name__ == "__main__":
    unittest.main()
