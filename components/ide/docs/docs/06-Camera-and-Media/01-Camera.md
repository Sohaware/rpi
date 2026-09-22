# USB Camera and Images

CodyNick AI discovers the USB webcam and stores pictures under `/home/client/images`.
Named examples reuse one input filename so repeated runs do not fill the folder.

```python
from codynick_ai import CodyNickAI

ai = CodyNickAI(workspace="/home/client", camera_index=0)
try:
    picture = ai.take_picture("my_picture")
    print(picture)
finally:
    ai.close()
```

`take_picture()` releases the camera after a one-shot capture. For several pictures in
one session, pass `keep_open=True`, then explicitly release it:

```python
for number in range(5):
    ai.take_picture("sequence", keep_open=True)
ai.close_camera()
```

When a CodyNick connection is available, `cody=cody, get_ready_sound=True` adds the
countdown and shutter feedback used by the bundled examples.

If the webcam LED remains on after a program has stopped, another process may own it.
See **Troubleshooting**.

