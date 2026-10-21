import time
import CodyNick

cody = CodyNick.Simulator()

# Add Joystick, Ultrasonic and Soil moisture to the stage first.
while True:
    joystick = CodyNick.Joystick.states(cody, 'Stand-Alone')
    distance = CodyNick.Ultrasonic_Sensor.read(cody, 'Stand-Alone')
    moisture = CodyNick.Soil_Moisture_Sensor.read(cody)

    print('Joystick:', joystick, 'Distance:', distance, 'cm', 'Soil:', moisture)

    if distance is not None:
        if distance < 20:
            CodyNick.RGB_Matrix.set(cody, 0, '#FF0000')
        else:
            CodyNick.RGB_Matrix.set(cody, 0, '#00FF00')

    if 'CLICK' in joystick:
        CodyNick.CJP_Sound_Maker.play(cody, 'C7', 100)

    time.sleep(0.3)
