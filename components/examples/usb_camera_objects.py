"""CodyNick USB-camera and YOLO acceptance test, release 0.3.0."""
import json
from pathlib import Path
from codynick_ai import CodyNickAI

candidates = []
for node in sorted(Path('/sys/class/video4linux').glob('video*')):
    if '/usb' in str((node / 'device').resolve()):
        candidates.append(int(node.name[5:]))
if not candidates:
    raise RuntimeError('No USB camera detected. Connect a USB webcam and run again.')

ai = None
for index in candidates:
    candidate = CodyNickAI(workspace='/home/client', camera_index=index)
    try:
        candidate.open_camera()
        ai = candidate
        print(f'\x1b[92mUSB camera /dev/video{index} opened\x1b[0m', flush=True)
        break
    except Exception as error:
        print(f'/dev/video{index}: {error}', flush=True)
        candidate.close()
if ai is None:
    raise RuntimeError('USB video nodes found, but none returned an image.')

try:
    picture = ai.take_picture('usb_camera_test')
    print('Picture:', picture, flush=True)
    print('Loading YOLO nano...', flush=True)
    print(ai.load_app('yolo', model='nano'), flush=True)
    result = ai.detect_objects('usb_camera_test')
    print(json.dumps(result, indent=2), flush=True)
    print('Open Images in the IDE to inspect the photo and results.', flush=True)
finally:
    ai.close()
