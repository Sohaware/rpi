# Stand-Alone Joystick Test

Move the joystick or press it. The live terminal prints the detected state.

```python
import time
import CodyNick

cody = CodyNick.CN()

while True:
    state = CodyNick.Joystick.states(cody, "Stand-Alone")
    if state:
        print(state)
    time.sleep(0.2)
```

Test `UP`, `RIGHT`, `DOWN`, `LEFT`, and `CLICK`. If one direction never appears,
check the gadget and its cable.
