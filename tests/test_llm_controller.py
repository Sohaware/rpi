import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "components/ai"))
sys.modules.setdefault("cv2", types.SimpleNamespace())

from codynick_ai import CodyNickAI
import codynick_ai.controller as controller


class Response:
    def __init__(self, body=b"{}", status=200):
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class LocalLlmTests(unittest.TestCase):
    def test_explicit_stt_loader_uses_the_existing_worker_loader(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            ai = CodyNickAI(workspace=temp)
            expected = {"app": "stt", "model_name": "small"}
            with patch.object(ai, "_load_stt", return_value=expected) as loader:
                result = ai.load_stt(model="small", language="en")
            self.assertEqual(result, expected)
            loader.assert_called_once_with(
                model="small", language="en", preload=None
            )

    def test_explicit_load_reuse_ask_and_unload(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            base = Path(temp)
            server = base / "llama-server"
            model = base / "model.gguf"
            server.write_text("runtime")
            model.write_text("model")
            process = MagicMock()
            process.poll.return_value = None
            answer = json.dumps({
                "choices": [{"message": {"content": "A short answer."}}]
            }).encode()
            with patch.object(controller.subprocess, "Popen", return_value=process) as popen, \
                 patch.object(controller.urllib.request, "urlopen", side_effect=[Response(), Response(answer)]):
                ai = CodyNickAI(
                    workspace=base,
                    llm_server=server,
                    llm_model=model,
                    load_timeout=2,
                )
                loaded = ai.load_llm()
                again = ai.load_llm()
                self.assertFalse(loaded["already_loaded"])
                self.assertTrue(again["already_loaded"])
                self.assertEqual(ai.ask("Question?"), "A short answer.")
                self.assertEqual(popen.call_count, 1)
                ai.unload_llm()
            process.terminate.assert_called_once_with()

    def test_ask_requires_explicit_load(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            ai = CodyNickAI(workspace=temp)
            with self.assertRaisesRegex(Exception, "LLM_NOT_LOADED"):
                ai.ask("Hello")


if __name__ == "__main__":
    unittest.main()
