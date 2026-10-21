import time
import CodyNick

cody = CodyNick.Simulator()

# Add the LED matrix to the stage first.
CodyNick.LED_Matrix.clear(cody)
for pixel in range(8):
    CodyNick.LED_Matrix.on(cody, pixel, pixel)
    time.sleep(0.2)

time.sleep(2)
CodyNick.LED_Matrix.clear(cody)

for speed in ['slow', 'medium', 'fast']:
    print('Scrolling:', speed)
    CodyNick.LED_Matrix.display_text(cody, 'Hi!', speed)
    time.sleep(8)

cody.close()
