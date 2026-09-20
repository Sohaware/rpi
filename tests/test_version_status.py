import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "version_status", ROOT / "installer/version_status.py"
)
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)


class VersionStatusTests(unittest.TestCase):
    def test_examples_report_current_modified_and_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            examples = Path(temp)
            current = examples / "current.py"
            modified = examples / "modified.py"
            current.write_text("current")
            modified.write_text("changed")
            (examples / "extra.py").write_text("unexpected")
            manifest = {"files": {
                "components/examples/current.py": hashlib.sha256(
                    current.read_bytes()).hexdigest(),
                "components/examples/modified.py": "a" * 64,
                "components/examples/missing.py": "b" * 64,
                "components/client/CodyNick.py": "c" * 64,
            }}
            with patch.object(status, "EXAMPLES", examples):
                results = {item["name"]: item["status"]
                           for item in status.example_statuses(manifest)}
        self.assertEqual(results, {
            "current.py": "current",
            "extra.py": "unexpected",
            "missing.py": "missing",
            "modified.py": "modified",
        })


if __name__ == "__main__":
    unittest.main()
