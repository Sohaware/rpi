import time
import CodyNick

cody = CodyNick.Simulator()

# Add Temperature, Seven-segment and LED matrix to the stage first.
CodyNick.LED_Matrix.display_text(cody, 'Temperature', 'fast')

while True:
    temperature = CodyNick.Temperature_Sensor.read(cody)
    if temperature is not None:
        temperature = round(temperature, 1)
        CodyNick.Seven_Segment.display(cody, 'Stand-Alone', temperature)

        if temperature < 20:
            color = '#0000FF'
        elif temperature <= 30:
            color = '#00FF00'
        else:
            color = '#FF0000'

        CodyNick.RGB_Matrix.set(cody, 0, color)
        print('Temperature:', temperature)

    time.sleep(0.5)
