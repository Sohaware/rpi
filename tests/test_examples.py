"""Exercise student demos without a camera, models, or native AI dependencies."""
import contextlib
import io
from pathlib import Path
import runpy
import types
import unittest
from unittest.mock import MagicMock, patch

EXAMPLES = Path(__file__).resolve().parents[1] / 'components/examples'


class ExampleTests(unittest.TestCase):
    def execute(self, name, detections=None, failure=False, nodes=True):
        ai = MagicMock()
        ai.detect_objects.return_value = {
            'detections': detections or [], 'annotated_image': '/images/results/demo.jpg'}
        if failure:
            ai.detect_objects.side_effect = RuntimeError('model failure')
        factory = MagicMock(return_value=ai)
        node = MagicMock()
        node.name = 'video0'
        node.__truediv__.return_value.resolve.return_value = '/sys/devices/usb1/video0'
        output = io.StringIO()
        with patch.dict('sys.modules', {'codynick_ai': types.SimpleNamespace(CodyNickAI=factory)}), \
             patch.object(Path, 'glob', return_value=[node] if nodes else []), \
             patch('time.sleep'), contextlib.redirect_stdout(output):
            script = runpy.run_path(str(EXAMPLES / name))
            try:
                script['main']()
            except RuntimeError:
                if not (failure or not nodes):
                    raise
                if failure:
                    ai.close.assert_called_once()
                else:
                    factory.assert_not_called()
                return ai, output.getvalue()
            if failure or not nodes:
                self.fail('Expected a clear error')
        ai.close.assert_called_once()
        return ai, output.getvalue()

    def test_camera_objects_and_zero_detections(self):
        ai, output = self.execute('camera_objects.py')
        self.assertIn('No objects detected', output)
        self.assertTrue(ai.take_picture.call_args.args[0].startswith('camera_objects_'))
        _, output = self.execute('camera_objects.py', [{'class_name': 'cup', 'confidence': .8}])
        self.assertIn('cup: score 0.80', output)

    def test_counter_counts_target_per_frame(self):
        ai, output = self.execute('object_counter.py', [
            {'class_name': 'bottle'}, {'class_name': 'cup'}, {'class_name': 'bottle'}])
        self.assertIn('[2, 2, 2, 2, 2]', output)
        self.assertEqual(len({call.args[0] for call in ai.take_picture.call_args_list}), 5)

    def test_comparison_same_photo_sequential_models(self):
        ai, output = self.execute('model_comparison.py')
        self.assertEqual([call.kwargs['model'] for call in ai.load_app.call_args_list],
                         ['nano', 'small', 'medium'])
        self.assertEqual(ai.unload_app.call_count, 3)
        self.assertEqual(ai.take_picture.call_count, 1)
        calls = ai.detect_objects.call_args_list
        self.assertEqual(len(calls), 15)
        self.assertEqual(len({call.args[0] for call in calls}), 1)
        self.assertEqual([call.kwargs['output_suffix'] for call in calls if 'output_suffix' in call.kwargs],
                         ['objects_nano', 'objects_small', 'objects_medium'])
        self.assertIn('not an accuracy benchmark', output)

    def test_missing_camera_and_worker_errors(self):
        for name in ('camera_objects.py', 'object_counter.py', 'model_comparison.py'):
            with self.subTest(name=name):
                self.execute(name, nodes=False)
                self.execute(name, failure=True)

    def test_camera_ocr_prints_text_confidence_and_outputs(self):
        ai = MagicMock()
        ai.read_text.return_value = {
            "text": "HELLO CODY NICK",
            "items": [{"confidence": 0.8}, {"confidence": 0.9}],
            "annotated_image": "/home/client/images/results/text_ocr.jpg",
            "json_result": "/home/client/images/results/text_ocr.json",
        }
        factory = MagicMock(return_value=ai)
        node = MagicMock()
        node.name = "video0"
        node.__truediv__.return_value.resolve.return_value = "/sys/devices/usb1/video0"
        output = io.StringIO()
        with patch.dict("sys.modules", {"codynick_ai": types.SimpleNamespace(CodyNickAI=factory)}), \
             patch.object(Path, "glob", return_value=[node]), contextlib.redirect_stdout(output):
            script = runpy.run_path(str(EXAMPLES / "camera_read_text.py"))
            script["main"]()
        ai.load_app.assert_called_once_with("ocr", model="standard", languages=["en"])
        self.assertEqual(ai.read_text.call_args.kwargs["preprocessing"], "scene")
        self.assertIn("HELLO CODY NICK", output.getvalue())
        self.assertIn("average confidence: 0.85", output.getvalue())
        self.assertIn("JSON result", output.getvalue())
        ai.close.assert_called_once()

    def test_voice_commands_set_colors_and_clean_up(self):
        events = iter([
            {"accepted": False},
            {"accepted": True, "matched_command": "green", "confidence": 0.91},
            {"accepted": True, "matched_command": "lights off", "confidence": 0.88},
            {"accepted": True, "matched_command": "stop listening", "confidence": 0.95},
        ])
        listener = MagicMock()
        listener.__iter__.return_value = events
        ai = MagicMock()
        ai.listen.return_value = listener
        cody = MagicMock()
        cody.ensure_connected.return_value = True
        matrix = MagicMock()
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=MagicMock(return_value=ai)),
            "CodyNick": types.SimpleNamespace(
                CN=MagicMock(return_value=cody), RGB_Matrix=matrix
            ),
        }
        output = io.StringIO()
        with patch.dict("sys.modules", modules), contextlib.redirect_stdout(output):
            script = runpy.run_path(str(EXAMPLES / "voice_led_colors.py"))
            script["main"]()
        ai.load_app.assert_called_once_with("stt", model="small", language="en")
        ai.listen.assert_called_once()
        self.assertEqual(matrix.set.call_count, 16)
        self.assertEqual(matrix.set.call_args.args[2], "#00FF00")
        self.assertEqual(matrix.clear.call_count, 2)
        listener.stop.assert_called_once()
        ai.close.assert_called_once()
        cody.close.assert_called_once()
        self.assertIn("Heard: green", output.getvalue())

    def test_voice_demo_releases_resources_after_failure(self):
        ai = MagicMock()
        ai.load_app.side_effect = RuntimeError("speech failure")
        cody = MagicMock()
        cody.ensure_connected.return_value = True
        matrix = MagicMock()
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=MagicMock(return_value=ai)),
            "CodyNick": types.SimpleNamespace(
                CN=MagicMock(return_value=cody), RGB_Matrix=matrix
            ),
        }
        with patch.dict("sys.modules", modules):
            script = runpy.run_path(str(EXAMPLES / "voice_led_colors.py"))
            with self.assertRaisesRegex(RuntimeError, "speech failure"):
                script["main"]()
        ai.close.assert_called_once()
        cody.close.assert_called_once()
        matrix.clear.assert_called_once_with(cody)


if __name__ == '__main__':
    unittest.main()
