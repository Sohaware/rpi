import time
import Dashboard

Dashboard.clear()

counter = Dashboard.Card(
    "info",
    "Counter",
    color="green",
    value=0,
    font_size=64,
    font_name="Arial",
    horizontal_alignment="center",
    vertical_alignment="center"
)

number = 0

while True:
    counter.set(number)
    number = number + 1
    time.sleep(2.5)
