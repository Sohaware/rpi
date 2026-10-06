import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("llm_setup_test", ROOT / "installer/llm_setup.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class LlmSetupTests(unittest.TestCase):
    def test_runtime_archive_rejects_traversal(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            base = Path(temp)
            archive = base / "bad.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                member = tarfile.TarInfo("llama-b10689/../../escape")
                member.size = 1
                bundle.addfile(member, io.BytesIO(b"x"))
            with patch.object(m, "RUNTIME_ROOT", base / "opt/llama-b10689"), \
                 self.assertRaisesRegex(RuntimeError, "Unexpected"):
                m.restore_runtime(archive)

    def test_model_identity_is_fixed(self):
        self.assertEqual(m.VERSION, "0.8.1")
        self.assertEqual(m.MODEL_PATH.name, "gemma-3-1b-it-Q4_K_M.gguf")


if __name__ == "__main__":
    unittest.main()
