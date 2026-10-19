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
    column_span=3
)

history = []

while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    temperature = round(temperature, 1)

    temperature_card.set(temperature)

    history.append(temperature)
    history = history[-20:]
    history_card.set(history)

    time.sleep(2.5)
