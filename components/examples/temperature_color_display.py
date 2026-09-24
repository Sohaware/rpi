"""Show temperature on the seven-segment display and use LEDs as a color indicator."""
import time
import CodyNick


cody = CodyNick.CN()


while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    temperature = round(temperature, 1)

    CodyNick.Seven_Segment.display(cody, "Stand-Alone", temperature)

    if temperature < 20:
        color = "#0000FF"
    elif temperature <= 30:
        color = "#00FF00"
    else:
        color = "#FF0000"

    for led in range(16):
        CodyNick.RGB_Matrix.set(cody, led, color)

    print("Temperature:", temperature, "C")
    time.sleep(1)
