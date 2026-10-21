"""Only the connection differs from the physical CodyJoy Pro demo."""
import time
import CodyNick

cody = CodyNick.Simulator()
last_action = ''

for led in range(16):
    CodyNick.RGB_Matrix.set(cody, led, '#00FF00')
    time.sleep(0.08)
time.sleep(1)
CodyNick.RGB_Matrix.clear(cody)
CodyNick.CJP_Sound_Maker.play_until_done(cody, 'C6', 150)
CodyNick.CJP_Sound_Maker.play_until_done(cody, 'E6', 150)
CodyNick.CJP_Sound_Maker.play_until_done(cody, 'G6', 250)
print('Hold a joystick arrow in the Simulator page, or press its center.')

while True:
    joystick = CodyNick.Joystick.states(cody, 'CJP')
    action = joystick[0] if joystick else ''

    if action and action != last_action:
        CodyNick.RGB_Matrix.clear(cody)
        if action == 'UP':
            leds, color, note = [15, 14, 13, 12], '#0000FF', 'C7'
        elif action == 'RIGHT':
            leds, color, note = [12, 11, 4, 3], '#00FF00', 'E7'
        elif action == 'DOWN':
            leds, color, note = [0, 1, 2, 3], '#FF0000', 'G7'
        elif action == 'LEFT':
            leds, color, note = [15, 8, 7, 0], '#FFFF00', 'B7'
        else:
            leds, color, note = [9, 10, 6, 5], '#FFFFFF', 'C8'
        for led in leds:
            CodyNick.RGB_Matrix.set(cody, led, color)
        CodyNick.CJP_Sound_Maker.play(cody, note, 150)
        print(action, note)
    last_action = action
    time.sleep(0.05)
