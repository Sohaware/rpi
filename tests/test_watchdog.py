import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location("watchdog", Path(__file__).parents[1] / "components/watchdog/service.py")
m = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"security": MagicMock()}):
    spec.loader.exec_module(m)


class WatchdogTests(unittest.TestCase):
    def cycle(self, old, new, failure=False):
        with patch.object(m, "block_python_file_if_intrusion_detected", return_value=True), \
             patch.object(Path, "exists", return_value=True), \
             patch.object(m, "calculate_sha256", return_value=new), \
             patch.object(m, "read_previous_hash", return_value=old), \
             patch.object(m, "write_current_hash") as write, \
             patch.object(m, "write_log_output"), \
             patch.object(m, "restart_service", side_effect=RuntimeError("failed") if failure else None) as restart, \
             patch.object(m.time, "sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                m.main()
            return restart.call_count, write.call_count

    def test_changed_script_restarts(self):
        self.assertEqual(self.cycle("old", "new"), (1, 1))

    def test_unchanged_script_does_not_restart(self):
        self.assertEqual(self.cycle("same", "same"), (0, 1))

    def test_first_start_seeds_hash(self):
        self.assertEqual(self.cycle(None, "new"), (0, 1))

    def test_failed_restart_keeps_previous_hash_for_retry(self):
        self.assertEqual(self.cycle("old", "new", failure=True), (1, 0))
