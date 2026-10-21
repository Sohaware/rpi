import time
import CodyNick

cody = CodyNick.Simulator()

# Add Wi-Fi / IoT to the stage. All names/keys below are fake demo values.
CodyNick.WiFi_IoT.set_wifi(cody, 'demo-network', 'demo-only')
CodyNick.WiFi_IoT.set_iot(cody, 'demo-user', 'demo-device', 'demo-key')

counter = 0
while True:
    counter += 1
    accepted = CodyNick.WiFi_IoT.write_int(cody, 0, counter)
    remote_switch = CodyNick.WiFi_IoT.read_bool(cody, 1)

    print('Status:', CodyNick.WiFi_IoT.status(cody), 'Counter accepted:', accepted,
          'Remote bool[1]:', remote_switch)

    if remote_switch:
        CodyNick.RGB_Matrix.set(cody, 0, '#0000FF')
    else:
        CodyNick.RGB_Matrix.set(cody, 0, '#00FF00')

    time.sleep(1)
