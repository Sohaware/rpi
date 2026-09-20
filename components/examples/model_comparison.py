"""CodyNick 0.5.2 demo: compare three YOLO models on one photo."""
from statistics import median
from time import perf_counter
from pathlib import Path
from uuid import uuid4
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


MODELS = ('nano', 'small', 'medium')
REPEATS = 3
CONFIDENCE = 0.35


def main():
    cody = CodyNick.CN()
    ai = None
    rows = []
    try:
        if not cody.ensure_connected():
            raise RuntimeError('CodyNick gadget not found. Connect it and run again.')
        ai = open_usb_camera()
        name = 'comparison_' + uuid4().hex[:12]
        print('Picture:', ai.take_picture(
            name, cody=cody, get_ready_sound=True), flush=True)
        ai.close_camera()
        print('Comparing one photo at the same confidence threshold.', flush=True)
        print('Times measure complete detection calls, not just model inference.', flush=True)
        for model in MODELS:
            print(f'Loading {model} (larger models may take longer)...', flush=True)
            started = perf_counter()
            ai.load_app('yolo', model=model)
            load_seconds = perf_counter() - started
            # Exclude an extra untimed detection from the measurements.
            ai.detect_objects(name, confidence=CONFIDENCE, save_visual=False)
            times = []
            for _ in range(REPEATS):
                started = perf_counter()
                result = ai.detect_objects(name, confidence=CONFIDENCE, save_visual=False)
                times.append(perf_counter() - started)
            saved = ai.detect_objects(name, confidence=CONFIDENCE,
                                      output_suffix=f'objects_{model}')
            rows.append((model, load_seconds, median(times), len(result['detections'])))
            print('Annotated picture:', saved['annotated_image'], flush=True)
            ai.unload_app()
        print('\nModel       Load (s)   Median call (s)   Objects', flush=True)
        for model, load, seconds, count in rows:
            print(f'{model:<10} {load:>9.2f} {seconds:>17.3f} {count:>9}', flush=True)
        print('More detections or higher scores do not prove better accuracy.', flush=True)
        print('This is a small demo, not an accuracy benchmark with labelled data.', flush=True)
    finally:
        if ai is not None:
            ai.close()
        cody.close()


if __name__ == '__main__':
    main()
