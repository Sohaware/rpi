"""CodyNick Examples 0.3.1: photograph and identify everyday objects."""
from pathlib import Path
from uuid import uuid4
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


def main():
    ai = open_usb_camera()
    try:
        name = 'camera_objects_' + uuid4().hex[:12]
        print('Picture:', ai.take_picture(name), flush=True)
        print('Loading YOLO nano...', flush=True)
        ai.load_app('yolo', model='nano')
        result = ai.detect_objects(name)
        detections = result['detections']
        print(f'Found {len(detections)} objects:', flush=True)
        for item in detections:
            print(f"  {item['class_name']}: score {item['confidence']:.2f}", flush=True)
        if not detections:
            print('No objects detected. Try a bottle, cup, or chair in good light.', flush=True)
        print('Annotated picture:', result['annotated_image'], flush=True)
        print('See Images and its results folder in the IDE.', flush=True)
    finally:
        ai.close()


if __name__ == '__main__':
    main()

