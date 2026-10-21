import time
import CodyNick

cody = CodyNick.Simulator()

CodyNick.Seven_Segment.display(cody, 'Stand-Alone', 25)
time.sleep(2)

CodyNick.Seven_Segment.display(cody, 'Stand-Alone', 21.1)
time.sleep(2)

CodyNick.Seven_Segment.display(cody, 'Stand-Alone', -5)
time.sleep(2)

CodyNick.Seven_Segment.display(cody, 'Stand-Alone', 10000)
time.sleep(2)

for number in range(1, 11):
    CodyNick.Seven_Segment.display(cody, 'Stand-Alone', number)
    time.sleep(0.5)

print('Finished. The display stays at 10.')
cody.close()
