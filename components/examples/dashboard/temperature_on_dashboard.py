import math
import time
import CodyNick
import Dashboard

cody = CodyNick.CN()

Dashboard.clear()

temperature_card = Dashboard.Card(
    "gauge",
    "Temperature",
    color="green",
    min_value=0,
    max_value=50,
    value=0,
    font_size=32,
    font_name="Arial",
    horizontal_alignment="center",
    vertical_alignment="center"
)

history_card = Dashboard.Card(
    "graph",
    "Temperature History",
    color="blue",
    value=[],
    column_span=3,
    x_axis_label="Time (s)",
    y_axis_label="Temperature (°C)"
)

history = []
Cnt = 0
started = time.monotonic()

while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    Cnt += 1

    if temperature is not None:
        temperature = round(temperature, 1)

        if not math.isnan(temperature):
            print(f"{Cnt} : {temperature}")

            temperature_card.set(temperature)

            seconds = round(time.monotonic() - started, 1)
            history.append([seconds, temperature])
            history = history[-20:]
            history_card.set(history)

    time.sleep(2.5)
