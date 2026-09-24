"""Show temperature on the seven-segment display and use LEDs as a color indicator."""
import time
import CodyNick


cody = CodyNick.CN()

alarm_enabled = True
was_clicked = False


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

    is_clicked = CodyNick.Joystick.click(cody, "CJP")

    if is_clicked and not was_clicked:
        alarm_enabled = not alarm_enabled

        if alarm_enabled:
            print("Alarm enabled")
        else:
            print("Alarm inhibited")

    was_clicked = is_clicked

    if temperature > 30 and alarm_enabled:
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "C6", 120)
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "E6", 120)
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "G6", 120)
        CodyNick.CJP_Sound_Maker.play_until_done(cody, "E6", 120)

    print("Temperature:", temperature, "C")
    time.sleep(0.3)
