# Gadget Simulator

Open **Gadget Simulator** from the main device page, or visit `http://10.42.0.1/simulator/`. Use your Pi's LAN address when not connected to its hotspot. No physical gadgets are required. The browser runs the graphics; Python still runs on the RPi.

## Build a Stage

CodyJoy Pro is permanently available. Drag gadgets from the toolbox onto the stage, or click their toolbox buttons. Move gadgets by their title bars; select one and use the cross button to remove it. Use **Fit stage** to see all gadgets or **1:1** for full-size controls. The stage scrolls independently. Layout and simulated sensor settings survive reboot.

Available gadgets: CJP (RGB LEDs, joystick and buzzer), Stand-Alone joystick, temperature sensor, Stand-Alone ultrasonic sensor, soil-moisture sensor, Stand-Alone seven-segment display, 8x8 LED matrix and Wi-Fi/IoT gadget. One instance of each can work together. UltraSeg, RFID and motion are not simulated yet.

## Run Examples

In the IDE, open **CodyNick examples/simulator**. Add the required gadgets before choosing **Run This File**.

| Example | Add to the stage |
|---|---|
| `simulator_demo.py` | Nothing: CJP is always present. Enable browser sound first. |
| `simulator_seven_segment.py` | Seven-segment |
| `simulator_gadgets_together.py` | Temperature, Seven-segment, LED matrix |
| `simulator_matrix_test.py` | LED matrix |
| `simulator_sensors.py` | Joystick, Ultrasonic, Soil moisture |
| `simulator_wifi_iot.py` | Wi-Fi / IoT |

Change sensor controls while the code is running. The temperature demo updates the display and colors CJP LED 0 blue below 20 C, green at 20-30 C, and red above 30 C while the matrix scrolls text.

Only the connection changes in your Python code:

```python
import CodyNick

cody = CodyNick.Simulator()
CodyNick.RGB_Matrix.set(cody, 0, '#00FF00')
```

Use `CodyNick.CN()` for physical hardware. The simulator never falls back to real serial ports. Keep personal files outside CodyNick examples: upgrades replace the examples folder.

## Stop Before Changing Gadgets

Only one Python simulator script and one control browser should be used at a time. To unlock the toolbox while a script is running, stop the script through SSH:

```bash
sudo systemctl stop script.service
```

Within about three seconds, Python shows Waiting. Add/remove gadgets, then choose Run This File again. A dedicated Stop button is not included yet. Missing-gadget errors are shown on the stage and in Python output.

## Display and Sensor Details

- LEDs have the same serpentine numbering as the physical CJP.
- The seven-segment display fits four digits, including the minus sign; decimal points do not consume a digit. Overflow shows dashes.
- The 8x8 matrix uses a crisp 5x7 bitmap font. Text scrolls one column at a time at three speeds. `LED_Matrix.on/off/set_pixel/clear` support individual pixels, with (0,0) at the top left.
- Temperature is adjustable from -55 to 125 C, ultrasonic distance from 2 to 400 cm, and soil moisture from 0 to 100 percent.
- Stand-Alone and CJP joysticks are independent. Hold arrows/center for input. Inputs release after focus loss or a stale connection.
- Enable sound with a browser click. Audio comes from that browser's speakers, not the physical buzzer.

## Offline Wi-Fi/IoT

This is a local, offline protocol model: no routers, cloud service or other devices are contacted, and Pi networking is never changed. Use fake demo credentials only. The gadget shows simulated Wi-Fi/cloud availability and typed variables. Python configuration makes the virtual module connect immediately when its availability toggles allow it.

There are indices 0-3 for each type (int, float, bool, string). The current Python read frame returns at most six payload characters. Credentials and variables remain in memory, not in the saved layout; they reset with the simulator service. Availability toggles are saved. Ordinary typed writes/reads are supported; `verify=True` is not part of the simulator's supported interface.

In `simulator_wifi_iot.py`, counter int[0] changes every second. Set Bool index 1 to true in the gadget and press Set value to turn CJP LED 0 blue; false restores green. Toggle connection availability to test disconnections.

## Version, Repair and Downgrade

Run `codynick-version` for the installed version. Use the usual fixed setup command for repair or upgrade. If a release has a problem, the maintainer can select an earlier original release on GitHub; rerun that same command to downgrade. The simulator service is disabled when the selected release does not include it. Saved stage files are retained for later reuse. This does not roll back Ubuntu packages, firmware or user data.

The simulator is intended for trusted local networks only. Do not expose its port 8091 or the IDE to the Internet.
