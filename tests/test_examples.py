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
        cody = MagicMock()
        cody.ensure_connected.return_value = True
        node = MagicMock()
        node.name = 'video0'
        node.__truediv__.return_value.resolve.return_value = '/sys/devices/usb1/video0'
        output = io.StringIO()
        modules = {
            'codynick_ai': types.SimpleNamespace(CodyNickAI=factory),
            'CodyNick': types.SimpleNamespace(CN=MagicMock(return_value=cody)),
        }
        with patch.dict('sys.modules', modules), \
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
                cody.close.assert_called_once()
                return ai, cody, output.getvalue()
            if failure or not nodes:
                self.fail('Expected a clear error')
        ai.close.assert_called_once()
        cody.close.assert_called_once()
        for capture in ai.take_picture.call_args_list:
            self.assertIs(capture.kwargs['cody'], cody)
            self.assertTrue(capture.kwargs['get_ready_sound'])
        return ai, cody, output.getvalue()

    def test_camera_objects_and_zero_detections(self):
        ai, _, output = self.execute('camera_objects.py')
        self.assertIn('No objects detected', output)
        self.assertEqual(ai.take_picture.call_args.args[0], 'camera_objects')
        _, _, output = self.execute(
            'camera_objects.py', [{'class_name': 'cup', 'confidence': .8}])
        self.assertIn('cup: score 0.80', output)

    def test_counter_counts_target_per_frame(self):
        ai, _, output = self.execute('object_counter.py', [
            {'class_name': 'bottle'}, {'class_name': 'cup'}, {'class_name': 'bottle'}])
        self.assertIn('[2, 2, 2, 2, 2]', output)
        self.assertEqual({call.args[0] for call in ai.take_picture.call_args_list},
                         {'object_counter'})
        self.assertTrue(all(call.kwargs['keep_open']
                            for call in ai.take_picture.call_args_list))
        ai.close_camera.assert_called_once()

    def test_comparison_same_photo_sequential_models(self):
        ai, _, output = self.execute('model_comparison.py')
        self.assertEqual([call.kwargs['model'] for call in ai.load_app.call_args_list],
                         ['nano', 'small', 'medium'])
        self.assertEqual(ai.unload_app.call_count, 3)
        self.assertEqual(ai.take_picture.call_count, 1)
        self.assertEqual(ai.take_picture.call_args.args[0], 'model_comparison')
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
        cody = MagicMock()
        cody.ensure_connected.return_value = True
        node = MagicMock()
        node.name = "video0"
        node.__truediv__.return_value.resolve.return_value = "/sys/devices/usb1/video0"
        output = io.StringIO()
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=factory),
            "CodyNick": types.SimpleNamespace(CN=MagicMock(return_value=cody)),
        }
        with patch.dict("sys.modules", modules), \
             patch.object(Path, "glob", return_value=[node]), contextlib.redirect_stdout(output):
            script = runpy.run_path(str(EXAMPLES / "camera_read_text.py"))
            script["main"]()
        ai.load_app.assert_called_once_with("ocr", model="standard", languages=["en"])
        self.assertEqual(ai.take_picture.call_args.args[0], "camera_text")
        self.assertEqual(ai.read_text.call_args.kwargs["confidence"], 0.20)
        self.assertEqual(ai.read_text.call_args.kwargs["preprocessing"], "scene")
        self.assertIn("HELLO CODY NICK", output.getvalue())
        self.assertIn("average confidence: 0.85", output.getvalue())
        self.assertIn("JSON result", output.getvalue())
        self.assertIs(ai.take_picture.call_args.kwargs["cody"], cody)
        self.assertTrue(ai.take_picture.call_args.kwargs["get_ready_sound"])
        ai.close.assert_called_once()
        cody.close.assert_called_once()

    def test_joystick_ocr_sets_green_for_normalized_codynick(self):
        ai = MagicMock()
        ai.read_text.return_value = {
            "text": "Welcome to Cody Nick!",
            "annotated_image": "/home/client/images/results/ocr.jpg",
            "json_result": "/home/client/images/results/ocr.json",
        }
        cody = MagicMock()
        cody.ensure_connected.return_value = True
        matrix = MagicMock()
        joystick = MagicMock()
        joystick.states.side_effect = [[], ["UP"]]
        node = MagicMock()
        node.name = "video0"
        node.__truediv__.return_value.resolve.return_value = "/sys/devices/usb1/video0"
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=MagicMock(return_value=ai)),
            "CodyNick": types.SimpleNamespace(
                CN=MagicMock(return_value=cody), RGB_Matrix=matrix, Joystick=joystick
            ),
        }
        output = io.StringIO()
        with patch.dict("sys.modules", modules), patch.object(Path, "glob", return_value=[node]), \
             patch("time.sleep") as sleep, contextlib.redirect_stdout(output):
            script = runpy.run_path(str(EXAMPLES / "joystick_ocr_led.py"))
            script["main"]()
        ai.take_picture.assert_called_once()
        self.assertIs(ai.take_picture.call_args.kwargs["cody"], cody)
        self.assertTrue(ai.take_picture.call_args.kwargs["get_ready_sound"])
        self.assertEqual(ai.take_picture.call_args.args[0], "joystick_ocr")
        self.assertEqual(ai.read_text.call_args.kwargs["confidence"], 0.20)
        ai.load_app.assert_called_once_with("ocr", model="standard", languages=["en"])
        self.assertEqual(matrix.set.call_count, 16)
        self.assertTrue(all(call.args[2] == "#00FF00" for call in matrix.set.call_args_list))
        self.assertIn("CODYNICK FOUND", output.getvalue())
        self.assertIn("Text match score: 1.00", output.getvalue())
        sleep.assert_any_call(5)
        self.assertGreaterEqual(matrix.clear.call_count, 3)
        ai.close.assert_called_once()
        cody.close.assert_called_once()

    def test_joystick_ocr_sets_red_when_text_is_absent(self):
        ai = MagicMock()
        ai.read_text.return_value = {
            "text": "Something else",
            "annotated_image": "/home/client/images/results/ocr.jpg",
            "json_result": "/home/client/images/results/ocr.json",
        }
        cody = MagicMock()
        cody.ensure_connected.return_value = True
        matrix = MagicMock()
        joystick = MagicMock()
        joystick.states.return_value = ["UP"]
        node = MagicMock()
        node.name = "video0"
        node.__truediv__.return_value.resolve.return_value = "/sys/devices/usb1/video0"
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=MagicMock(return_value=ai)),
            "CodyNick": types.SimpleNamespace(
                CN=MagicMock(return_value=cody), RGB_Matrix=matrix, Joystick=joystick
            ),
        }
        with patch.dict("sys.modules", modules), patch.object(Path, "glob", return_value=[node]), \
             patch("time.sleep") as sleep:
            script = runpy.run_path(str(EXAMPLES / "joystick_ocr_led.py"))
            script["main"]()
        self.assertIs(ai.take_picture.call_args.kwargs["cody"], cody)
        self.assertTrue(ai.take_picture.call_args.kwargs["get_ready_sound"])
        self.assertEqual(matrix.set.call_count, 16)
        self.assertTrue(all(call.args[2] == "#FF0000" for call in matrix.set.call_args_list))
        sleep.assert_any_call(5)
        self.assertGreaterEqual(matrix.clear.call_count, 3)

    def test_joystick_ocr_match_tolerates_one_character_error(self):
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=MagicMock()),
            "CodyNick": types.SimpleNamespace(),
        }
        with patch.dict("sys.modules", modules):
            script = runpy.run_path(str(EXAMPLES / "joystick_ocr_led.py"))
        self.assertEqual(script["text_match_score"]("Welcome CodyNlck", "codynick"),
                         0.875)
        self.assertGreaterEqual(
            script["text_match_score"]("Welcome CodyNlck", "codynick"),
            script["MATCH_SIMILARITY"],
        )

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

    def test_create_speech_generates_once_and_keeps_named_file(self):
        ai = MagicMock()
        ai.audio_exists.return_value = False
        ai.load_app.return_value = {"ok": True}
        ai.tts.return_value = {
            "ok": True,
            "audio_file": "/home/client/audio/welcome_message.wav",
        }
        modules = {
            "codynick_ai": types.SimpleNamespace(
                CodyNickAI=MagicMock(return_value=ai)
            )
        }
        with patch.dict("sys.modules", modules):
            script = runpy.run_path(str(EXAMPLES / "create_speech_file.py"))
            script["main"]()
        ai.load_app.assert_called_once_with("tts", model="fast", language="en")
        ai.tts.assert_called_once_with(
            script["TEXT"], "welcome_message", speaker="speaker1"
        )
        ai.close.assert_called_once()

    def test_create_speech_does_not_regenerate_existing_audio(self):
        ai = MagicMock()
        ai.audio_exists.return_value = True
        modules = {
            "codynick_ai": types.SimpleNamespace(
                CodyNickAI=MagicMock(return_value=ai)
            )
        }
        with patch.dict("sys.modules", modules):
            script = runpy.run_path(str(EXAMPLES / "create_speech_file.py"))
            script["main"]()
        ai.load_app.assert_not_called()
        ai.tts.assert_not_called()
        ai.close.assert_called_once()

    def test_play_saved_audio_does_not_load_tts(self):
        ai = MagicMock()
        ai.audio_exists.return_value = True
        ai.speak.return_value = {
            "ok": True,
            "audio_file": "/home/client/audio/welcome_message.wav",
        }
        modules = {
            "codynick_ai": types.SimpleNamespace(
                CodyNickAI=MagicMock(return_value=ai)
            )
        }
        with patch.dict("sys.modules", modules):
            script = runpy.run_path(str(EXAMPLES / "play_saved_audio.py"))
            script["main"]()
        ai.load_app.assert_not_called()
        ai.speak.assert_called_once_with("welcome_message")
        ai.close.assert_called_once()

    def test_conversation_generator_replaces_27_paused_answers(self):
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=MagicMock())
        }
        with patch.dict("sys.modules", modules):
            script = runpy.run_path(
                str(EXAMPLES / "generate_conversation_answers.py")
            )
        answers = script["ANSWERS"]
        self.assertEqual(sum(len(items) for items in answers.values()), 27)
        self.assertTrue(all(text.startswith(";;;")
                            for items in answers.values() for text in items))
        source = (EXAMPLES / "generate_conversation_answers.py").read_text()
        self.assertIn("STAGING_FOLDER.replace(ANSWER_FOLDER)", source)
        self.assertIn("shutil.rmtree(ANSWER_FOLDER, ignore_errors=True)", source)
        self.assertIn("ai.delete_audio(name)", source)
        self.assertIn("shutil.copy2(source, destination)", source)

    def test_voice_conversation_session_and_cache_rules(self):
        modules = {
            "codynick_ai": types.SimpleNamespace(CodyNickAI=MagicMock()),
            "CodyNick": types.SimpleNamespace(),
        }
        with patch.dict("sys.modules", modules):
            script = runpy.run_path(str(EXAMPLES / "voice_conversation.py"))
        self.assertEqual(script["QUESTION_TIMEOUT"], 10.0)
        self.assertEqual(script["QUESTION_TOPICS"]["sleep"], "sleep")
        self.assertEqual(script["QUESTION_TOPICS"]["go to sleep"], "sleep")
        for phrase in ("good morning", "good afternoon", "good evening", "good night"):
            self.assertEqual(script["QUESTION_TOPICS"][phrase], "greeting")
        source = (EXAMPLES / "voice_conversation.py").read_text()
        self.assertIn('playback_name = f"{PLAYBACK_PREFIX}{selected.stem}"', source)
        self.assertIn("No speech for 10 seconds", source)
        self.assertIn('if topic == "sleep":', source)
        self.assertIn("while True:\n                listening_effect(cody)", source)


if __name__ == '__main__':
    unittest.main()
