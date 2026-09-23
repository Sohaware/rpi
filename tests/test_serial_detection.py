import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]


def load_library():
    serial = types.ModuleType("serial")
    tools = types.ModuleType("serial.tools")
    list_ports = types.ModuleType("serial.tools.list_ports")
    list_ports.comports = MagicMock(return_value=[])
    tools.list_ports = list_ports
    serial.tools = tools
    serial.Serial = MagicMock()
    keyboard = types.ModuleType("keyboard")
    requests = types.ModuleType("requests")
    with patch.dict(sys.modules, {
        "serial": serial,
        "serial.tools": tools,
        "serial.tools.list_ports": list_ports,
        "keyboard": keyboard,
        "requests": requests,
    }):
        spec = importlib.util.spec_from_file_location(
            "codynick_serial_test", ROOT / "components/client/CodyNick.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


m = load_library()


def port(device, description="test", vid=None, pid=None):
    return types.SimpleNamespace(
        device=device, description=description, vid=vid, pid=pid
    )


class SerialDetectionTests(unittest.TestCase):
    def detector(self):
        return object.__new__(m.CN)

    def test_only_usb_serial_candidates_are_accepted(self):
        self.assertTrue(m.CN._is_usb_serial_port(port("/dev/ttyUSB0")))
        self.assertTrue(m.CN._is_usb_serial_port(port("/dev/ttyACM1")))
        self.assertTrue(m.CN._is_usb_serial_port(port("COM7", vid=0x1234, pid=0x5678)))
        self.assertFalse(m.CN._is_usb_serial_port(port("/dev/ttyAMA0")))
        self.assertFalse(m.CN._is_usb_serial_port(port("/dev/ttyS0")))

    def test_uses_fixed_delay_and_first_exact_identity(self):
        wrong = MagicMock()
        wrong.read_line.return_value = "CN@@SOMETHING-ELSE"
        valid = MagicMock()
        valid.read_line.return_value = "CN@@CJP-Neo" + "\0" * 9
        ports = [port("/dev/ttyAMA0"), port("/dev/ttyUSB0"), port("/dev/ttyACM0")]

        with patch.object(m.serial.tools.list_ports, "comports", return_value=ports), \
             patch.object(m, "SerialPort", side_effect=[wrong, valid]) as serial_port, \
             patch.object(m.time, "sleep") as sleep, \
             patch.object(m.time, "monotonic", side_effect=[10.0, 12.0, 14.1]):
            result = self.detector()._auto_detect_serial()

        self.assertIs(result, valid)
        self.assertEqual(
            [call.kwargs["port"] for call in serial_port.call_args_list],
            ["/dev/ttyUSB0", "/dev/ttyACM0"],
        )
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2.0, 2.0])
        wrong.close_serial.assert_called_once_with()
        valid.close_serial.assert_not_called()
        valid.read_line.assert_called_once_with(timeout=1.0, max_bytes=64)

    def test_rejected_device_is_closed_and_no_port_is_cached(self):
        candidate = MagicMock()
        candidate.read_line.return_value = "CN@@"
        usb = port("/dev/ttyUSB3")
        detector = self.detector()

        for _ in range(2):
            with patch.object(m.serial.tools.list_ports, "comports", return_value=[usb]), \
                 patch.object(m, "SerialPort", return_value=candidate), \
                 patch.object(m.time, "sleep"), \
                 self.assertRaisesRegex(RuntimeError, "No CodyJoy Pro"):
                detector._auto_detect_serial()

        self.assertEqual(candidate.close_serial.call_count, 2)
        self.assertFalse(hasattr(detector, "saved_port"))


if __name__ == "__main__":
    unittest.main()
