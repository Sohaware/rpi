"""CodyNick 0.5.3 demo: count a chosen object in five separate photos."""
import time
from pathlib import Path
import CodyNick
from codynick_ai import CodyNickAI


def open_usb_camera():
    nodes = sorted(Path('/sys/class/video4linux').glob('video*'))
    candidates = [int(node.name[5:]) for node in nodes
                  if '/usb' in str((node / 'device').resolve())]
    if not candidates:
        raise RuntimeError('No USB webcam found. Connect it and run again.')
    for index in candidates:
        ai = CodyNickAI(workspace='/home/client', camera_index=index)
        try:
            ai.open_camera()
            print(f'\x1b[92mUSB camera /dev/video{index} opened\x1b[0m', flush=True)
            return ai
        except Exception as error:
            print(f'/dev/video{index}: {error}', flush=True)
            ai.close()
    raise RuntimeError('No USB camera returned an image. Check whether it is in use.')


TARGET = 'bottle'  # Use a YOLO label, such as person, cup, chair, or bottle.
SAMPLES = 5
INTERVAL_SECONDS = 2
CONFIDENCE = 0.35


def main():
    cody = CodyNick.CN()
    ai = None
    counts = []
    try:
        if not cody.ensure_connected():
            raise RuntimeError('CodyNick gadget not found. Connect it and run again.')
        ai = open_usb_camera()
        print(f'Counting {TARGET!r} per photo, not unique objects over time.', flush=True)
        ai.load_app('yolo', model='nano')
        for index in range(SAMPLES):
            name = 'object_counter'
            ai.take_picture(name, cody=cody, get_ready_sound=True)
            result = ai.detect_objects(name, confidence=CONFIDENCE)
            count = sum(item['class_name'] == TARGET for item in result['detections'])
            counts.append(count)
            print(f'Photo {index + 1}/{SAMPLES}: {count} {TARGET}(s)', flush=True)
            print('Annotated picture:', result['annotated_image'], flush=True)
            if index + 1 < SAMPLES:
                time.sleep(INTERVAL_SECONDS)
        if counts:
            print(f'Per-photo counts: {counts}; maximum in one photo: {max(counts)}', flush=True)
    finally:
        if ai is not None:
            ai.close()
        cody.close()


if __name__ == '__main__':
    main()
