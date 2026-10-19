import contextlib
import copy
import io
from pathlib import Path
import types
import unittest
from unittest.mock import patch


EXAMPLE = Path(__file__).resolve().parents[1] / 'components/examples/dashboard/temperature_on_dashboard.py'


class Finished(Exception):
    pass


class TemperatureDashboardTests(unittest.TestCase):
    def run_example(self, samples):
        state = {'index': 0}
        cards = []

        class Card:
            def __init__(self, *args, **kwargs):
                self.updates = []
                self.options = kwargs
                cards.append(self)

            def set(self, value):
                self.updates.append(copy.deepcopy(value))

        def sleep(seconds):
            self.assertEqual(seconds, 2.5)
            state['index'] += 1
            if state['index'] == len(samples):
                raise Finished()

        modules = {
            'time': types.SimpleNamespace(sleep=sleep, monotonic=lambda: 100 + state['index'] * 2.5),
            'CodyNick': types.SimpleNamespace(CN=lambda: object(), Temperature_Sensor=types.SimpleNamespace(read=lambda cody: samples[state['index']])),
            'Dashboard': types.SimpleNamespace(clear=lambda: None, Card=Card),
        }
        with patch.dict('sys.modules', modules), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(Finished):
                exec(compile(EXAMPLE.read_text(encoding='utf-8'), str(EXAMPLE), 'exec'), {})
        return cards

    def test_missing_zero_and_high_readings_leave_cards_unchanged(self):
        gauge, graph = self.run_example([None, 0, 120, 2395915000, -2, 20.6])
        self.assertEqual(gauge.updates, [-2, 20.6])
        self.assertEqual(graph.updates[-1], [[10.0, -2], [12.5, 20.6]])
        self.assertEqual(graph.options['x_axis_label'], 'Time (s)')

    def test_latest_twenty_samples_keep_original_elapsed_seconds(self):
        gauge, graph = self.run_example([20] * 25)
        self.assertEqual(len(graph.updates[-1]), 20)
        self.assertEqual(graph.updates[-1][0][0], 12.5)
        self.assertEqual(graph.updates[-1][-1][0], 60.0)

    def test_filter_is_applied_after_rounding_as_requested(self):
        gauge, graph = self.run_example([0.04, 119.96, 119.94, -0.1])
        self.assertEqual(gauge.updates, [119.9, -0.1])


if __name__ == '__main__':
    unittest.main()
