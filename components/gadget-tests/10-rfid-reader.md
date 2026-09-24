# RFID Reader Test

Move a compatible card or tag close to the reader.

```python
import time
import CodyNick

cody = CodyNick.CN()

while True:
    uid = CodyNick.RFID_Reader.readuid(cody)
    if uid:
        print("RFID UID:", uid)
    time.sleep(0.5)
```

The terminal should print the tag UID. Test more than one tag to confirm that their
identifiers differ.
