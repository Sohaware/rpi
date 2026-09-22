# Dashboard Interaction Patterns

The browser polls the database approximately every two seconds. `sync()` performs a
new database query; it does not wait for a change. Avoid tight loops.

## Switch or slider input

```python
import time
import Dashboard

fan = Dashboard.Card("switch", "Fan", value=False)
level = Dashboard.Card("slider", "Level", min_value=0, max_value=100, value=50)

try:
    while True:
        fan.sync()
        level.sync()
        fan_on = str(fan.value).strip().lower() == "true"
        requested_level = float(level.value)
        print(fan_on, requested_level)
        time.sleep(0.5)
finally:
    fan.delete()
    level.delete()
```

## Momentary button

```python
button = Dashboard.Card("button", "Take Reading", value=False)

while True:
    button.sync()
    if str(button.value).lower() == "true":
        take_reading()
        button.set(False)  # re-enable the browser button
    time.sleep(0.2)
```

The value is a level, not an event queue. Several fast clicks can merge into one. Reset
the button only after processing its action.

## Separate command and reported state

Do not let browser and Python continuously write different meanings into one card.
Use separate cards where appropriate:

```python
requested = Dashboard.Card("slider", "Requested speed",  min_value=0, max_value=100, value=0)
actual = Dashboard.Card("gauge", "Actual speed", min_value=0, max_value=100, value=0)
```

Call `sync()` immediately before interpreting browser-controlled values. Use `set()`
for device-reported cards. Avoid changing other attributes and calling `save()` after a
browser update unless the local value has first been synchronized.

