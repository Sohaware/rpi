"""Test CodyJoy Pro joystick directions, RGB matrix sides, and high buzzer notes."""
import time
import CodyNick


cody = CodyNick.CN()
last_action = ""


while True:
    joystick = CodyNick.Joystick.states(cody, "CJP")
    action = ""

    if "CLICK" in joystick:
        action = "CLICK"
    elif "UP" in joystick:
        action = "UP"
    elif "RIGHT" in joystick:
        action = "RIGHT"
    elif "DOWN" in joystick:
        action = "DOWN"
    elif "LEFT" in joystick:
        action = "LEFT"

    if action and action != last_action:
        CodyNick.RGB_Matrix.clear(cody)

        if action == "UP":
            leds = [15, 14, 13, 12]
            color = "#0000FF"
            note = "C7"
        elif action == "RIGHT":
            leds = [12, 11, 4, 3]
            color = "#00FF00"
            note = "E7"
        elif action == "DOWN":
            leds = [0, 1, 2, 3]
            color = "#FF0000"
            note = "G7"
        elif action == "LEFT":
            leds = [15, 8, 7, 0]
            color = "#FFFF00"
            note = "B7"
        else:
            leds = [9, 10, 6, 5]
            color = "#FFFFFF"
            note = "C8"

        for led in leds:
            CodyNick.RGB_Matrix.set(cody, led, color)

        CodyNick.CJP_Sound_Maker.play_until_done(cody, note, 150)

        print(action, note)
        last_action = action

    time.sleep(0.1)
