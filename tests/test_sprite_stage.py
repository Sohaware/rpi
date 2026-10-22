import importlib.util
import math
from pathlib import Path
import threading
import time
import sys
import unittest
from http.server import ThreadingHTTPServer
import urllib.request
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sprite_server', ROOT / 'components/sprite-stage/server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
spec = importlib.util.spec_from_file_location('SpriteStage', ROOT / 'components/client/SpriteStage.py')
bridge = importlib.util.module_from_spec(spec)
sys.modules['SpriteStage'] = bridge
spec.loader.exec_module(bridge)
SpriteStage = bridge.SpriteStage


class StageTests(unittest.TestCase):
    def test_installer_configures_stage_and_disables_it_on_downgrade(self):
        spec=importlib.util.spec_from_file_location('sprite_installer', ROOT/'installer/app_setup.py')
        installer=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for components,enabled in [({'sprite-stage':'1.0.0'},True),({},False)]:
            directory=MagicMock()
            with patch.object(installer,'run') as run, patch.object(installer,'deploy') as deploy, \
                 patch.object(installer,'safe_destination',return_value=directory):
                installer.configure_sprite_stage({'components':components},Path('/backup'))
                if enabled:
                    deploy.assert_called_once()
                    run.assert_any_call('systemctl','enable','--now','codynick-sprite-stage.service')
                    directory.mkdir.assert_called_once_with(parents=True,exist_ok=True)
                else:
                    deploy.assert_not_called()
                    directory.mkdir.assert_not_called()
                    run.assert_called_once_with('systemctl','disable','--now','codynick-sprite-stage.service',check=False)

    def test_bounce_uses_sprite_size_and_does_not_flip_when_heading_away(self):
        stage=server.Stage()
        stage.command({'action':'go','x':240,'y':0})
        result=stage.command({'action':'bounce'})
        self.assertAlmostEqual(result['x'],216)
        self.assertEqual(result['direction'],270)
        self.assertEqual(stage.command({'action':'bounce'})['direction'],270)
        stage.command({'action':'set_size','size':200})
        stage.command({'action':'point','direction':45})
        stage.command({'action':'go','x':240,'y':180})
        self.assertEqual(stage.command({'action':'bounce'})['direction'],225)

    def test_timed_speech_mouse_and_axis_setters(self):
        stage=server.Stage()
        self.assertEqual(stage.command({'action':'set_x','x':20})['x'],20)
        self.assertEqual(stage.command({'action':'set_y','y':30})['y'],30)
        with patch.object(server.time,'monotonic',return_value=100):
            stage.command({'action':'say','text':'Hello','seconds':2})
            stage.command({'action':'keys','keys':[],'mouse':{'x':60,'y':-20,'down':True}})
        with patch.object(server.time,'monotonic',return_value=100.5):
            self.assertEqual(stage.snapshot()['speech'],'Hello')
            self.assertTrue(stage.snapshot()['mouse']['down'])
        with patch.object(server.time,'monotonic',return_value=103):
            self.assertEqual(stage.snapshot()['speech'],'')
            self.assertFalse(stage.snapshot()['mouse']['down'])

    def test_glide_is_timed_and_finishes_at_exact_destination(self):
        client=object.__new__(SpriteStage)
        with patch.object(client,'_state',return_value={'x':0,'y':0}), \
             patch.object(client,'go') as go, \
             patch('SpriteStage.time.monotonic',side_effect=[0,0,0,.5,.5,1]), \
             patch('SpriteStage.time.sleep'):
            client.glide(1,100,50)
            self.assertEqual(go.call_args_list[-1].args,(100,50))
            self.assertEqual(len(go.call_args_list),3)
        with self.assertRaises(ValueError):client.glide(-1,0,0)

    def test_direction_size_and_axis_changes(self):
        stage=server.Stage()
        self.assertEqual(stage.command({'action':'point','direction':-90})['direction'],270)
        self.assertEqual(stage.command({'action':'change_x','amount':20})['x'],20)
        state=stage.command({'action':'change_y','amount':-30})
        self.assertEqual((state['x'],state['y']),(20,-30))
        self.assertEqual(stage.command({'action':'set_size','size':150})['size'],150)
        self.assertEqual(stage.command({'action':'change_size','size':-25})['size'],125)
        self.assertEqual(stage.command({'action':'change_size','size':-1000})['size'],10)
        self.assertEqual(stage.command({'action':'set_size','size':1000})['size'],300)

    def test_motion_bounds_and_keys(self):
        stage = server.Stage()
        self.assertEqual(stage.command({'action':'move','steps':10})['x'],10)
        stage.command({'action':'turn','degrees':90})
        self.assertAlmostEqual(stage.command({'action':'move','steps':10})['y'],-10)
        self.assertEqual(stage.command({'action':'move','steps':1000})['y'],-180)
        stage.command({'action':'keys','keys':['right']})
        self.assertEqual(stage.snapshot()['keys'],['right'])
        with patch.object(server.time,'monotonic',return_value=time.monotonic()+2):
            self.assertEqual(stage.snapshot()['keys'],[])
        for command in [{'action':'execute','code':'x'}, {'action':'go','x':float('nan'),'y':0}, {'action':'keys','keys':['bad']}]:
            with self.assertRaises(ValueError):stage.command(command)

    def test_visibility_and_speech(self):
        stage=server.Stage()
        self.assertFalse(stage.command({'action':'hide'})['visible'])
        self.assertTrue(stage.command({'action':'show'})['visible'])
        self.assertEqual(len(stage.command({'action':'say','text':'x'*999})['speech']),200)

if __name__=='__main__':unittest.main()
