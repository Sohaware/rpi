import json
import os
import keyboard
import threading
import serial
import serial.tools.list_ports
import time
from typing import Optional
import requests, shutil
from datetime import datetime

__version__ = "1.20.1"

# update 18-11-2025 03

# environment/storage functions
LOG_FILE = os.environ.get(
    "CODYNICK_LOG_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.log"),
)

def log(x):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", buffering=1) as f:
        f.write(f"[{timestamp}] {x}\n")


def UpdateLib():
    UPDATE_URL = "https://download.codynick.com/uploads/UPGRD/CodyNick.py"
    SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CodyNick.py")
    response = requests.get(UPDATE_URL)
    if response.status_code == 200:
        temp_path = SCRIPT_PATH + ".new"
        with open(temp_path, "wb") as f:
            f.write(response.content)
        # Replace old script with new one
        shutil.move(temp_path, SCRIPT_PATH)
        log("Update applied successfully.")
    else:
        log("Failed to download update.")
    exit()

    


class SerialPort:
    def __init__(
        self,
        port: str,
        baud: int = 115200,
        timeout: float = 0.1,
    ) -> None:
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            timeout=timeout,
            write_timeout=1,
        )
        time.sleep(0.5)  # wait for board reset (common for Arduino-like devices)
        self.ser = ser

    def flush(self):
        """
        Clear input and output buffers.
        """
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except Exception:
            pass

    def send_line(self, text: str, add_newline: bool = False) -> None:
        """
        Send text over serial.
        If add_newline is True, append '\n' before sending.
        Otherwise send exactly the bytes of 'text' as-is.
        """
        if add_newline and not text.endswith("\n"):
            text = text + "\n"
        self.ser.write(text.encode("utf-8"))
        self.ser.flush()

    def read_line(
        self,
        timeout: float = 1.0,
        max_bytes: int = 64,
        inter_char_timeout: float = 0.05,
    ) -> Optional[str]:
        """
        Read characters one-by-one (character-wise), not line-wise.

        We:
        - Read at most max_bytes.
        - Stop when no new characters arrive for 'inter_char_timeout' seconds
          OR when overall 'timeout' is reached.
        - Ignore any '\n' or '\r' that might appear.
        - Return a string without any '\n' or '\r', or None if nothing was read.
        """
        end_time = time.time() + timeout
        buf = bytearray()

        while time.time() < end_time and len(buf) < max_bytes:
            if self.ser.in_waiting > 0:
                chunk = self.ser.read(1)
                if not chunk:
                    continue

                # Ignore newline or carriage return if they ever appear
                if chunk in (b"\n", b"\r"):
                    continue

                buf.extend(chunk)

                # After we get a character, extend deadline slightly to allow
                # the rest of the response to arrive.
                end_time = time.time() + inter_char_timeout
            else:
                # No data waiting; sleep briefly to avoid busy loop
                time.sleep(0.005)

        if not buf:
            return None

        # Decode and make sure no '\n' or '\r' remain
        s = buf.decode("utf-8", errors="ignore")
        s = s.replace("\n", "").replace("\r", "")
        return s if s else None

    def close_serial(self):
        try:
            self.ser.close()
        except Exception:
            pass


class CN:
    RECONNECT_INTERVAL = 1.0

    def _auto_detect_serial(self, startup_delay: float = 2.0) -> SerialPort:
        """
        Scan available serial ports, send an identify command to each,
        and return a SerialPort connected to the first one that responds
        with a string starting with 'CN@@'.

        Probing command: exact 20-byte packet "CN@@IDENTIFY--------"
        (no '\\n' or '\\r').
        """
        IDENTIFY_COMMAND = "CN@@IDENTIFY--------"  # 20 chars
        IDENTIFY_PREFIX = "CN@@"
        IDENTIFY_TIMEOUT = 1.0  # seconds
        MAX_RESPONSE_BYTES = 64

        # Small delay for OS/device stabilization if needed
        time.sleep(startup_delay)

        ports = list(serial.tools.list_ports.comports())

        if not ports:
            print("[auto_detect_serial] No serial ports found.")
            raise RuntimeError("No serial ports found")

        # Show list of present ports
        print("[auto_detect_serial] Available serial ports:")
        for idx, info in enumerate(ports):
            print(f"  {idx}: {info.device} - {info.description}")

        # Probe each port
        for info in ports:
            port_name = info.device
            print(f"[auto_detect_serial] Probing port {port_name} ...")
            candidate = None

            try:
                candidate = SerialPort(port=port_name)
                time.sleep(3)

                # Clear buffers
                candidate.flush()

                # Send EXACTLY 20 bytes (no newline)
                # (IDENTIFY_COMMAND length is already 20)
                candidate.send_line(IDENTIFY_COMMAND, add_newline=False)

                # Read response character-wise
                response = candidate.read_line(
                    timeout=IDENTIFY_TIMEOUT,
                    max_bytes=MAX_RESPONSE_BYTES,
                )

                # Check if it looks like a CodyNick device
                if response and IDENTIFY_PREFIX in response: # response.startswith(IDENTIFY_PREFIX):
                    print(
                        f"\033[92m[auto_detect_serial] Found CodyNick device on {port_name}: {response}\033[0m"
                    )
                    return candidate

                # Not our device ? close and continue
                candidate.close_serial()

            except Exception as e:
                print(f"[auto_detect_serial] Failed probing {port_name}: {e}")
                try:
                    if candidate is not None:
                        candidate.close_serial()
                except Exception:
                    pass

        # If we reach here, nothing responded correctly
        raise RuntimeError(
            "No CodyNick-compatible serial device found (no response starting with 'CN@@')."
        )

    def __init__(self):
        self.ser = None
        self._last_reconnect_attempt = 0.0
        self._was_connected = False
        self._io_failures = 0
        self.connected_at = 0.0
        try:
            self.ser = self._auto_detect_serial()
            self._was_connected = self.ser is not None
            if self._was_connected:
                self.connected_at = time.time()
        except Exception as e:
            log("Error initializing Serial CodyNick Connection: " + str(e))

    def mark_disconnected(self):
        if self.ser is not None:
            try:
                self.ser.close_serial()
            except Exception:
                pass
        self.ser = None
        self._io_failures = 0
        self.connected_at = 0.0
        if self._was_connected:
            print("[CodyNick] Device disconnected.")
        self._was_connected = False

    def ensure_connected(self):
        if self.ser is not None:
            try:
                if self.ser.ser.is_open:
                    return True
            except Exception:
                self.mark_disconnected()

        now = time.time()
        if now - self._last_reconnect_attempt < self.RECONNECT_INTERVAL:
            return False

        self._last_reconnect_attempt = now
        try:
            self.ser = self._auto_detect_serial(startup_delay=0.0)
            if self.ser is not None:
                self._io_failures = 0
                self.connected_at = time.time()
                if not self._was_connected:
                    print("[CodyNick] Device connected.")
                self._was_connected = True
                return True
        except Exception as e:
            log("Error reconnecting Serial CodyNick Connection: " + str(e))
            self.ser = None

        return False

    def record_io_success(self):
        self._io_failures = 0

    def record_io_failure(self):
        self._io_failures += 1
        if self._io_failures >= 3:
            self.mark_disconnected()

    def close(self):
        try:
            if self.ser is not None:
                self.ser.close_serial()
            self.ser = None
            self = None
        except Exception:
            pass


class Memory:
    data = {}

    def __init__(self, name):
        try:
            os.mkdir("mem")
        except FileExistsError:
            pass
        self.name = name

        try:
            with open(f"mem/{name}.json", "r") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            with open(f"mem/{name}.json", "w") as f:
                f.write(json.dumps(self.data))

    def sync(self):
        with open(f"mem/{self.name}.json", "w") as f:
            f.write(json.dumps(self.data))


# USB HID functions - Keyboard emulator

class HID:
    def __init__(self):
        self.buffer = ""
        self._lock = threading.Lock()
        self._listener_thread = threading.Thread(
            target=self._start_listener, daemon=True
        )
        self._listener_thread.start()

    def _start_listener(self):
        keyboard.on_press(self._on_key)

    def _on_key(self, event):
        with self._lock:
            key = event.name
            if len(key) == 1:
                self.buffer += key
            elif key == "space":
                self.buffer += " "
            elif key == "enter":
                self.buffer += "\n"
            elif key == "backspace":
                self.buffer = self.buffer[:-1]

    def get(self):
        with self._lock:
            return self.buffer

    def clear(self):
        with self._lock:
            self.buffer = ""

    def len(self):
        with self._lock:
            return len(self.buffer)


# JoyStick functions
class Joystick:
    DEVICES = {
        "CJP": 5,
        "STANDALONE": 0,
    }
    SUPPORTED_INDICES = set(range(6))

    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    # Bit masks (must match Arduino gateway firmware) – copied from test_joystick.py
    DIRX   = 1
    DIRXP  = 2
    SPEEDX = 4

    DIRY   = 8
    DIRYP  = 16
    SPEEDY = 32

    CLICK  = 64

    @staticmethod
    def _resolve_device(device):
        if isinstance(device, int):
            return device

        text = str(device).strip()
        if text.isdigit():
            return int(text)

        key = text.upper().replace("-", "").replace("_", "").replace(" ", "")
        return Joystick.DEVICES.get(key)

    @staticmethod
    def _get_states(cody, device):
        """
        Return a human-readable joystick state list from one joystick device.
        """
        try:
            if cody is None or not cody.ensure_connected():
                return []
        except AttributeError:
            return []

        joystick_index = Joystick._resolve_device(device)
        if joystick_index not in Joystick.SUPPORTED_INDICES:
            log("Unknown joystick device: " + str(device))
            return []

        cmd = f"CN@@JOY@@{joystick_index:02d}".ljust(20, "_")
        header = f"CN@@JOY@@{joystick_index:02d}"

        try:
            cody.ser.flush()
            cody.ser.send_line(cmd, add_newline=False)
            response = cody.ser.read_line(timeout=0.25, max_bytes=20)
            if response and len(response) >= 20 and response.startswith(header):
                payload = response[len(header):].replace("_", "")
                cody.record_io_success()
                if payload == "N" or not payload:
                    return []
                state_map = {
                    "U": "UP",
                    "D": "DOWN",
                    "L": "LEFT",
                    "R": "RIGHT",
                    "C": "CLICK",
                }
                return [state_map[ch] for ch in payload if ch in state_map]
        except Exception as e:
            log("Error reading Joystick: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass

        try:
            cody.record_io_failure()
        except Exception:
            pass
        return []

    @staticmethod
    def position(cody, device, pos):
        """
        Return True if joystick is currently in the requested position.
        pos: "up", "down", "left", "right"
        """
        if pos not in ["up", "down", "left", "right"]:
            return False

        states = Joystick._get_states(cody, device)
        pos_map = {
            "up": "UP",
            "down": "DOWN",
            "left": "LEFT",
            "right": "RIGHT",
        }
        return pos_map[pos] in states

    @staticmethod
    def states(cody, device):
        """
        Return the current joystick states as a list:
        ["UP"], ["LEFT"], ["CLICK"], ["UP", "CLICK"], etc.
        """
        return Joystick._get_states(cody, device)

    @staticmethod
    def click(cody, device):
        """
        Return True if joystick button is pressed.
        """
        states = Joystick._get_states(cody, device)
        return "CLICK" in states


# LEX Mat functions
class LED_Matrix:
    SPEEDS = {
        "slow": 0,
        "medium": 1,
        "fast": 2,
    }
    COMMAND_DELAY = 0.003

    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def _resolve_speed(speed):
        if isinstance(speed, str):
            speed = speed.strip().lower()
            if speed in LED_Matrix.SPEEDS:
                return LED_Matrix.SPEEDS[speed]
            if speed.isdigit():
                speed = int(speed)

        try:
            speed = int(speed)
        except (TypeError, ValueError):
            return None

        return speed if speed in [0, 1, 2] else None

    @staticmethod
    def display_text(Cody, text, speed=1):
        try:
            if Cody is None or not Cody.ensure_connected():
                return

            speed = LED_Matrix._resolve_speed(speed)
            if speed is None:
                log("LED Matrix speed must be 0, 1, 2, slow, medium, or fast: " + str(speed))
                return

            text = str(text)
            try:
                text_bytes = text.encode("ascii")
            except UnicodeEncodeError:
                log("LED Matrix text must contain ASCII characters only.")
                return

            if len(text_bytes) > 49:
                log("LED Matrix text must be 49 characters or fewer.")
                return

            packet = f"CN@@LTXT@@{speed}{len(text_bytes):02d}".encode("ascii") + text_bytes
            Cody.ser.ser.write(packet)
            Cody.ser.ser.flush()
            time.sleep(LED_Matrix.COMMAND_DELAY)
        except Exception as e:
            log("Error sending text to LED Matrix: " + str(e))
            try:
                Cody.mark_disconnected()
            except Exception:
                pass

    @staticmethod
    def set_pixel(Cody, x, y, state):
        try:
            if Cody is None or not Cody.ensure_connected():
                return

            x = int(x)
            y = int(y)
            if x < 0 or x > 7 or y < 0 or y > 7:
                log(f"LED Matrix coordinates must be 0..7: ({x}, {y})")
                return

            state = 1 if bool(state) else 0
            packet = f"CN@@LPX@@{x}{y}{state}".ljust(20, "_")
            Cody.ser.send_line(packet, add_newline=False)
            time.sleep(LED_Matrix.COMMAND_DELAY)
        except Exception as e:
            log("Error setting LED Matrix pixel: " + str(e))
            try:
                Cody.mark_disconnected()
            except Exception:
                pass

    @staticmethod
    def on(Cody, x, y):
        LED_Matrix.set_pixel(Cody, x, y, True)

    @staticmethod
    def off(Cody, x, y):
        LED_Matrix.set_pixel(Cody, x, y, False)

    @staticmethod
    def clear(Cody):
        try:
            if Cody is None or not Cody.ensure_connected():
                return

            packet = "CN@@LCLR@@".ljust(20, "_")
            Cody.ser.send_line(packet, add_newline=False)
            time.sleep(LED_Matrix.COMMAND_DELAY)
        except Exception as e:
            log("Error clearing LED Matrix: " + str(e))
            try:
                Cody.mark_disconnected()
            except Exception:
                pass


# RGB Matrix functions
class RGB_Matrix:
    COMMAND_DELAY = 0.003
    XY_TO_LED = [
        [0, 1, 2, 3],
        [7, 6, 5, 4],
        [8, 9, 10, 11],
        [15, 14, 13, 12],
    ]
    PALETTE = {
        0: "#FF0000",
        1: "#00FFFF",
        2: "#0000FF",
        3: "#FFFF00",
        4: "#FF00FF",
        5: "#00FF00",
        6: "#FF8000",
        7: "#FFFFFF",
    }

    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def _resolve_color(color):
        if isinstance(color, int):
            if color not in RGB_Matrix.PALETTE:
                log("RGB Matrix color code must be 0..7: " + str(color))
                return None
            return RGB_Matrix.PALETTE[color]

        if isinstance(color, (list, tuple)):
            if len(color) != 3:
                log("RGB Matrix percentage color must have 3 values: " + str(color))
                return None

            rgb = []
            for value in color:
                try:
                    pct = float(value)
                except (TypeError, ValueError):
                    log("RGB Matrix percentage color values must be numbers: " + str(color))
                    return None

                if pct < 0 or pct > 100:
                    log("RGB Matrix percentage color values must be 0..100: " + str(color))
                    return None

                rgb.append(round(pct * 255 / 100))

            return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

        color = str(color).strip()
        if len(color) != 7 or color[0] != "#":
            log("RGB Matrix color must be #RRGGBB, color code 0..7, or [R%, G%, B%]: " + color)
            return None

        try:
            int(color[1:], 16)
        except ValueError:
            log("RGB Matrix color must be #RRGGBB, color code 0..7, or [R%, G%, B%]: " + color)
            return None

        return color

    @staticmethod
    def set(Cody, led, color):
        try:
            if Cody is None or not Cody.ensure_connected():
                return

            led = int(led)
            if led < 0 or led > 15:
                log("RGB Matrix LED index out of range: " + str(led))
                return

            color = RGB_Matrix._resolve_color(color)
            if color is None:
                return

            packet = f"CN@@RGB@@{led:02d}{color}".ljust(20, "_")
            Cody.ser.send_line(packet, add_newline=False)
            time.sleep(RGB_Matrix.COMMAND_DELAY)
        except Exception as e:
            log("Error sending to RGB Matrix: " + str(e))
            try:
                Cody.mark_disconnected()
            except Exception:
                pass

    @staticmethod
    def _xy_to_led(x, y):
        x = int(x)
        y = int(y)
        if x < 0 or x > 3 or y < 0 or y > 3:
            return None

        return RGB_Matrix.XY_TO_LED[y][x]

    @staticmethod
    def set_xy(Cody, x, y, color):
        led = RGB_Matrix._xy_to_led(x, y)
        if led is None:
            log(f"RGB Matrix XY out of range: ({x}, {y})")
            return

        RGB_Matrix.set(Cody, led, color)

    @staticmethod
    def clear(Cody):
        try:
            if Cody is None or not Cody.ensure_connected():
                return

            packet = "CN@@RGBCLR@@".ljust(20, "_")
            Cody.ser.send_line(packet, add_newline=False)
            time.sleep(RGB_Matrix.COMMAND_DELAY)
        except Exception as e:
            log("Error clearing RGB Matrix: " + str(e))
            try:
                Cody.mark_disconnected()
            except Exception:
                pass


# CodyJoy Pro Sound Maker functions
class CJP_Sound_Maker:
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    NOTE_FREQUENCIES = {
        "B0": 31,
        "C1": 33, "C#1": 35, "D1": 37, "D#1": 39, "E1": 41, "F1": 44, "F#1": 46,
        "G1": 49, "G#1": 52, "A1": 55, "A#1": 58, "B1": 62,
        "C2": 65, "C#2": 69, "D2": 73, "D#2": 78, "E2": 82, "F2": 87, "F#2": 93,
        "G2": 98, "G#2": 104, "A2": 110, "A#2": 117, "B2": 123,
        "C3": 131, "C#3": 139, "D3": 147, "D#3": 156, "E3": 165, "F3": 175, "F#3": 185,
        "G3": 196, "G#3": 208, "A3": 220, "A#3": 233, "B3": 247,
        "C4": 262, "C#4": 277, "D4": 294, "D#4": 311, "E4": 330, "F4": 349, "F#4": 370,
        "G4": 392, "G#4": 415, "A4": 440, "A#4": 466, "B4": 494,
        "C5": 523, "C#5": 554, "D5": 587, "D#5": 622, "E5": 659, "F5": 698, "F#5": 740,
        "G5": 784, "G#5": 831, "A5": 880, "A#5": 932, "B5": 988,
        "C6": 1047, "C#6": 1109, "D6": 1175, "D#6": 1245, "E6": 1319, "F6": 1397, "F#6": 1480,
        "G6": 1568, "G#6": 1661, "A6": 1760, "A#6": 1865, "B6": 1976,
        "C7": 2093, "C#7": 2217, "D7": 2349, "D#7": 2489, "E7": 2637, "F7": 2794, "F#7": 2960,
        "G7": 3136, "G#7": 3322, "A7": 3520, "A#7": 3729, "B7": 3951,
        "C8": 4186, "C#8": 4435, "D8": 4699, "D#8": 4978,
    }
    FLATS = {
        "DB": "C#",
        "EB": "D#",
        "GB": "F#",
        "AB": "G#",
        "BB": "A#",
    }
    COMMAND_DELAY = 0.003

    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def _note_to_frequency(note):
        note = str(note).strip().upper()
        if len(note) < 2:
            return None

        if len(note) >= 3 and note[1] in ["#", "B"]:
            name = note[:2]
            octave_text = note[2:]
        else:
            name = note[:1]
            octave_text = note[1:]

        name = CJP_Sound_Maker.FLATS.get(name, name)

        try:
            octave = int(octave_text)
        except ValueError:
            return None

        return CJP_Sound_Maker.NOTE_FREQUENCIES.get(f"{name}{octave}")

    @staticmethod
    def play(Cody, note, duration_ms):
        try:
            if Cody is None or not Cody.ensure_connected():
                return

            frequency = CJP_Sound_Maker._note_to_frequency(note)
            if frequency is None:
                log("CJP Sound Maker note must be from B0 to D#8: " + str(note))
                return

            duration_ms = int(duration_ms)
            if duration_ms <= 0 or duration_ms > 99999:
                log("CJP Sound Maker duration must be 1..99999 ms: " + str(duration_ms))
                return

            packet = f"CN@@BUZ@@{frequency:04d}{duration_ms:05d}".ljust(20, "_")
            Cody.ser.send_line(packet, add_newline=False)
            time.sleep(CJP_Sound_Maker.COMMAND_DELAY)
        except Exception as e:
            log("Error sending to CJP Sound Maker: " + str(e))
            try:
                Cody.mark_disconnected()
            except Exception:
                pass

    @staticmethod
    def play_until_done(Cody, note, duration_ms):
        CJP_Sound_Maker.play(Cody, note, duration_ms)
        try:
            time.sleep(int(duration_ms) / 1000)
        except Exception as e:
            log("Error waiting for CJP Sound Maker note: " + str(e))


# Motion Detection functions
class Motion_Detection:
    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def detect(cody):
        try:
            if cody is None or not cody.ensure_connected():
                return False
        except AttributeError:
            return False

        try:
            ser = cody.ser.ser
        except AttributeError:
            return False

        cmd = "CN@@PIR@@".ljust(20, "_").encode("utf-8")
        header = b"CN@@PIR@@"

        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        try:
            ser.write(cmd)
            ser.flush()

            start = time.time()
            buf = b""
            while time.time() - start < 0.25:
                ser.timeout = 0.02
                chunk = ser.read(5)
                if chunk:
                    buf += chunk
                    idx = buf.find(header)
                    if idx != -1 and idx + 20 <= len(buf):
                        cody.record_io_success()
                        return buf[idx + len(header)] == ord("1")

            cody.record_io_failure()
            return False
        except Exception as e:
            log("Error reading Motion Detection: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass
            return False


# Temperature Sensor functions
class Temperature_Sensor:
    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def read(cody):
        try:
            if cody is None or not cody.ensure_connected():
                return None
        except AttributeError:
            return None

        try:
            ser = cody.ser.ser
        except AttributeError:
            return None

        cmd = "CN@@TEMP@@".ljust(20, "_").encode("utf-8")
        header = b"CN@@TEMP@@"

        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        try:
            ser.write(cmd)
            ser.flush()

            start = time.time()
            buf = b""
            while time.time() - start < 0.25:
                ser.timeout = 0.02
                chunk = ser.read(5)
                if chunk:
                    buf += chunk
                    idx = buf.find(header)
                    if idx != -1 and idx + 20 <= len(buf):
                        raw = buf[idx + len(header):idx + 20]
                        value_text = raw.decode("utf-8", errors="ignore").split("_", 1)[0]
                        if value_text:
                            cody.record_io_success()
                            return float(value_text)

            cody.record_io_failure()
            return None
        except Exception as e:
            log("Error reading Temperature Sensor: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass
            return None


# Soil Moisture Sensor functions
class Soil_Moisture_Sensor:
    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def read(cody):
        try:
            if cody is None or not cody.ensure_connected():
                return None
        except AttributeError:
            return None

        try:
            ser = cody.ser.ser
        except AttributeError:
            return None

        cmd = "CN@@SOIL@@".ljust(20, "_").encode("utf-8")
        header = b"CN@@SOIL@@"

        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        try:
            ser.write(cmd)
            ser.flush()

            start = time.time()
            buf = b""
            while time.time() - start < 0.25:
                ser.timeout = 0.02
                chunk = ser.read(5)
                if chunk:
                    buf += chunk
                    idx = buf.find(header)
                    if idx != -1 and idx + 20 <= len(buf):
                        raw = buf[idx + len(header):idx + 20]
                        value_text = raw.decode("utf-8", errors="ignore").split("_", 1)[0]
                        if value_text:
                            cody.record_io_success()
                            return float(value_text)

            cody.record_io_failure()
            return None
        except Exception as e:
            log("Error reading Soil Moisture Sensor: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass
            return None


# RFID Reader functions
class RFID_Reader:
    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def readuid(cody):
        try:
            if cody is None or not cody.ensure_connected():
                return None
        except AttributeError:
            return None

        try:
            ser = cody.ser.ser
        except AttributeError:
            return None

        cmd = "CN@@RFID@@".ljust(20, "_").encode("utf-8")
        header = b"CN@@RFID@@"

        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        try:
            ser.write(cmd)
            ser.flush()

            start = time.time()
            buf = b""
            while time.time() - start < 0.25:
                ser.timeout = 0.02
                chunk = ser.read(5)
                if chunk:
                    buf += chunk
                    idx = buf.find(header)
                    if idx != -1 and idx + 20 <= len(buf):
                        raw = buf[idx + len(header):idx + 20]
                        uid = raw.decode("utf-8", errors="ignore").split("_", 1)[0]
                        if len(uid) == 8:
                            cody.record_io_success()
                            return uid

            cody.record_io_failure()
            return None
        except Exception as e:
            log("Error reading RFID Reader: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass
            return None


# Ultrasonic Sensor functions
class Ultrasonic_Sensor:
    DEVICES = {
        "STANDALONE": 0,
        "ULTRASEG": 1,
    }

    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def _resolve_device(device):
        if isinstance(device, int):
            return device

        text = str(device).strip()
        if text.isdigit():
            return int(text)

        key = text.upper().replace("-", "").replace("_", "").replace(" ", "")
        return Ultrasonic_Sensor.DEVICES.get(key)

    @staticmethod
    def read(cody, device):
        try:
            if cody is None or not cody.ensure_connected():
                return None
        except AttributeError:
            return None

        try:
            ser = cody.ser.ser
        except AttributeError:
            return None

        ultrasonic_index = Ultrasonic_Sensor._resolve_device(device)
        if ultrasonic_index not in [0, 1]:
            log("Unknown ultrasonic sensor device: " + str(device))
            return None

        cmd = f"CN@@ULTRA@@{ultrasonic_index:02d}".ljust(20, "_").encode("utf-8")
        header = f"CN@@ULTRA@@{ultrasonic_index:02d}".encode("utf-8")

        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        try:
            ser.write(cmd)
            ser.flush()

            start = time.time()
            buf = b""
            while time.time() - start < 0.25:
                ser.timeout = 0.02
                chunk = ser.read(5)
                if chunk:
                    buf += chunk
                    idx = buf.find(header)
                    if idx != -1 and idx + 20 <= len(buf):
                        raw = buf[idx + len(header):idx + 20]
                        value_text = raw.decode("utf-8", errors="ignore").split("_", 1)[0]
                        if value_text:
                            cody.record_io_success()
                            return float(value_text)

            cody.record_io_failure()
            return None
        except Exception as e:
            log("Error reading Ultrasonic Sensor: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass
            return None


# Seven-Segment functions
class Seven_Segment:
    COMMAND_DELAY = 0.003
    DEVICES = {
        "STANDALONE": 0,
        "ULTRASEG": 2,
    }

    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")
    
    @staticmethod
    def _resolve_device(device):
        if isinstance(device, int):
            return device

        text = str(device).strip()
        if text.isdigit():
            return int(text)

        key = text.upper().replace("-", "").replace("_", "").replace(" ", "")
        return Seven_Segment.DEVICES.get(key)

    @staticmethod
    def display(Cody, device, value):
        # value = str(value)
        # if ("." not in value and len(value) > 4): raise Exception("Value too long for 4-digit Seven Segment")
        # elif('.' in value and len(value) > 5): raise Exception("Value too long for 4-digit Seven Segment with decimal")
        f = float(value)
        if f < -999 or f > 9999:
            f = 10000  # out of range indicator, will be displayed as ----
        value = str(f)
        value_trimmed = value[:5]

        log(f"Float = {f}, value trimmed = {value_trimmed}")
        try:
            if Cody is None or not Cody.ensure_connected():
                return

            display_index = Seven_Segment._resolve_device(device)
            if display_index not in [0, 2]:
                log("Unknown Seven Segment device: " + str(device))
                return

            # while len(value) < 4:
            #     value = "0" + value
            # value = value+"0"*(10-len(value))  # pad to 10 chars

            value_trimmed = value_trimmed.ljust(8, '\0')
            log(f"value in function = {value_trimmed}")
            Cody.ser.send_line(f"CN@@7SEG@@{display_index:02d}{value_trimmed}", add_newline=False)
            time.sleep(Seven_Segment.COMMAND_DELAY)
        except Exception as e:
            log("Error sending to Seven Segment" + str(e))
            try:
                Cody.mark_disconnected()
            except Exception:
                pass


# WiFi and IoT functions
class WiFi_IoT:
    COMMAND_DELAY = 0.003
    IOT_WRITE_DELAY_SECONDS = 0.25
    FLOAT_VERIFY_TOLERANCE = 0.01
    STRING_VERIFY_CHARS = 6
    _last_wifi_keep_alive = 0.0
    _last_iot_keep_alive = 0.0
    _last_wifi_settings_check = 0.0
    _last_iot_settings_check = 0.0
    _last_wifi_target = None
    _last_iot_target = None
    _last_reported_wifi_connected = None
    _last_reported_iot_connected = None
    _last_reported_startup_wait = None
    TYPE_CODES = {
        "int": "0",
        "integer": "0",
        "float": "1",
        "bool": "2",
        "boolean": "2",
        "string": "3",
        "str": "3",
    }

    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def _read_frame(cody, header, timeout=0.5, expected_len=20, count_io_failure=False):
        start = time.time()
        buf = b""
        header_bytes = header.encode("utf-8")

        while time.time() - start < timeout:
            cody.ser.ser.timeout = 0.02
            chunk = cody.ser.ser.read(5)
            if chunk:
                chunk = chunk.replace(b"\n", b"").replace(b"\r", b"")
                buf += chunk
                idx = buf.find(header_bytes)
                if idx != -1 and idx + expected_len <= len(buf):
                    cody.record_io_success()
                    return buf[idx:idx + expected_len].decode("utf-8", errors="ignore")
            else:
                time.sleep(0.005)

        if count_io_failure:
            cody.record_io_failure()
        return None

    @staticmethod
    def _send_variable(cody, prefix, payload, response_header):
        try:
            if cody is None or not cody.ensure_connected():
                return None
        except AttributeError:
            return None

        try:
            text = prefix + payload
            text.encode("ascii")
            if len(text) > 53:
                log("WiFi/IoT command is too long: " + text[:20])
                return None

            cody.ser.flush()
            cody.ser.ser.write(text.encode("ascii"))
            cody.ser.ser.flush()
            time.sleep(WiFi_IoT.COMMAND_DELAY)
            return WiFi_IoT._read_frame(cody, response_header)
        except Exception as e:
            log("Error sending WiFi/IoT command: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass
            return None

    @staticmethod
    def _send_fixed(cody, packet, response_header, timeout=0.5, expected_len=20):
        try:
            if cody is None or not cody.ensure_connected():
                return None
        except AttributeError:
            return None

        try:
            cody.ser.flush()
            cody.ser.send_line(packet, add_newline=False)
            time.sleep(WiFi_IoT.COMMAND_DELAY)
            return WiFi_IoT._read_frame(cody, response_header, timeout=timeout, expected_len=expected_len)
        except Exception as e:
            log("Error sending WiFi/IoT command: " + str(e))
            try:
                cody.mark_disconnected()
            except Exception:
                pass
            return None

    @staticmethod
    def _set_field(cody, field, value):
        value = str(value)
        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            log("WiFi/IoT values must be ASCII text.")
            return False

        if len(value) > 40:
            log("WiFi/IoT values must be 40 characters or fewer.")
            return False

        response = WiFi_IoT._send_variable(
            cody,
            "CN@@WIFI@@",
            f"{field}{len(value):02d}{value}",
            "CN@@WOK@@",
        )
        return bool(response and len(response) >= 11 and response[9] == field and response[10] == "1")

    @staticmethod
    def _mask_secret(value):
        value = str(value)
        if not value:
            return ""
        if len(value) <= 2:
            return "*" * len(value)
        return value[0] + ("*" * (len(value) - 2)) + value[-1]

    @staticmethod
    def _wifi_label(ssid, password):
        return f"({ssid}/{WiFi_IoT._mask_secret(password)})"

    @staticmethod
    def _iot_label(username, device_id, device_key, cloud_mode):
        return f"({username}/{device_id}/{WiFi_IoT._mask_secret(device_key)}/{cloud_mode})"

    @staticmethod
    def _report_wifi_state(is_connected, label):
        if WiFi_IoT._last_reported_wifi_connected is is_connected:
            return
        WiFi_IoT._last_reported_wifi_connected = is_connected
        print("KeepAlive: " + ("WiFi connected " if is_connected else "WiFi disconnected ") + label)

    @staticmethod
    def _report_iot_state(is_connected, label):
        if WiFi_IoT._last_reported_iot_connected is is_connected:
            return
        WiFi_IoT._last_reported_iot_connected = is_connected
        print("KeepAlive: " + ("IoT connected " if is_connected else "IoT disconnected ") + label)

    @staticmethod
    def _startup_ready(cody, Tstartup, label):
        connected_at = getattr(cody, "connected_at", 0.0)
        if not connected_at:
            return True

        remaining = float(Tstartup) - (time.time() - connected_at)
        if remaining <= 0:
            WiFi_IoT._last_reported_startup_wait = None
            return True

        rounded_remaining = max(1, int(round(remaining)))
        report_key = (connected_at, rounded_remaining)
        if WiFi_IoT._last_reported_startup_wait != report_key:
            WiFi_IoT._last_reported_startup_wait = report_key
            print(f"KeepAlive: waiting {rounded_remaining}s for WiFi/IoT module startup {label}")
        return False

    @staticmethod
    def set_ssid(cody, ssid):
        return WiFi_IoT._set_field(cody, "S", ssid)

    @staticmethod
    def set_password(cody, password):
        return WiFi_IoT._set_field(cody, "P", password)

    @staticmethod
    def set_cloud_mode(cody, mode):
        return WiFi_IoT._set_field(cody, "M", int(mode))

    @staticmethod
    def set_username(cody, username):
        return WiFi_IoT._set_field(cody, "U", username)

    @staticmethod
    def set_device_id(cody, device_id):
        return WiFi_IoT._set_field(cody, "D", device_id)

    @staticmethod
    def set_device_key(cody, device_key):
        return WiFi_IoT._set_field(cody, "K", device_key)

    @staticmethod
    def set_wifi(cody, ssid, password):
        ssid_ok = WiFi_IoT.set_ssid(cody, ssid)
        password_ok = WiFi_IoT.set_password(cody, password)
        return ssid_ok and password_ok

    @staticmethod
    def set_iot(cody, username, device_id, device_key, cloud_mode=1):
        mode_ok = WiFi_IoT.set_cloud_mode(cody, cloud_mode)
        username_ok = WiFi_IoT.set_username(cody, username)
        device_id_ok = WiFi_IoT.set_device_id(cody, device_id)
        device_key_ok = WiFi_IoT.set_device_key(cody, device_key)
        return mode_ok and username_ok and device_id_ok and device_key_ok

    @staticmethod
    def _reset(cody, reset_type):
        response = WiFi_IoT._send_fixed(
            cody,
            f"CN@@WRST@@{reset_type}".ljust(20, "_"),
            "CN@@WOK@@",
            timeout=0.5,
        )
        return bool(
            response
            and len(response) >= 11
            and response[9] == reset_type
            and response[10] == "1"
        )

    @staticmethod
    def restart(cody):
        return WiFi_IoT._reset(cody, "E")

    @staticmethod
    def reset_wifi(cody):
        return WiFi_IoT._reset(cody, "W")

    @staticmethod
    def reset_iot(cody):
        return WiFi_IoT._reset(cody, "D")

    @staticmethod
    def keep_alive_wifi(cody, ssid, password, Trst=15, Tchk=10, Tstartup=10):
        ssid = str(ssid)
        password = str(password)
        target = (ssid, password)
        label = WiFi_IoT._wifi_label(ssid, password)
        if not WiFi_IoT._startup_ready(cody, Tstartup, label):
            return False

        now = time.time()
        must_check_settings = (
            target != WiFi_IoT._last_wifi_target
            or now - WiFi_IoT._last_wifi_settings_check >= float(Tchk)
        )

        if must_check_settings:
            WiFi_IoT._last_wifi_target = target
            WiFi_IoT._last_wifi_settings_check = now
            stored_ssid = WiFi_IoT.get_wifi_ssid(cody)
            stored_password = WiFi_IoT.get_wifi_password(cody)

            if stored_ssid != ssid or stored_password != password:
                print("KeepAlive: WiFi settings changed. Updating and resetting " + label)
                WiFi_IoT._last_wifi_keep_alive = now
                settings_ok = WiFi_IoT.set_wifi(cody, ssid, password)
                reset_ok = WiFi_IoT.reset_wifi(cody)
                if settings_ok and reset_ok:
                    print("KeepAlive: WiFi reset requested " + label)
                return False

        if WiFi_IoT.wifi_connected(cody):
            WiFi_IoT._report_wifi_state(True, label)
            return True
        WiFi_IoT._report_wifi_state(False, label)

        if now - WiFi_IoT._last_wifi_keep_alive < float(Trst):
            return False

        WiFi_IoT._last_wifi_keep_alive = now
        print("KeepAlive: WiFi not connected. Resetting WiFi " + label)
        WiFi_IoT.reset_wifi(cody)
        return False

    @staticmethod
    def keep_alive_iot(cody, username, device_id, device_key, cloud_mode=1, Trst=15, Tchk=10, Tstartup=10):
        username = str(username)
        device_id = str(device_id)
        device_key = str(device_key)
        cloud_mode = int(cloud_mode)
        label = WiFi_IoT._iot_label(username, device_id, device_key, cloud_mode)
        if not WiFi_IoT._startup_ready(cody, Tstartup, label):
            return False

        if not WiFi_IoT.wifi_connected(cody):
            if WiFi_IoT._last_reported_iot_connected is not False:
                print("KeepAlive: IoT waiting for WiFi " + label)
                WiFi_IoT._last_reported_iot_connected = False
            return False

        target = (username, device_id, device_key, cloud_mode)
        previous_target = WiFi_IoT._last_iot_target
        now = time.time()
        must_check_settings = (
            target != WiFi_IoT._last_iot_target
            or now - WiFi_IoT._last_iot_settings_check >= float(Tchk)
        )

        if must_check_settings:
            WiFi_IoT._last_iot_target = target
            WiFi_IoT._last_iot_settings_check = now
            stored_username = WiFi_IoT.get_username(cody)
            stored_device_id = WiFi_IoT.get_device_id(cody)
            stored_device_key = WiFi_IoT.get_device_key(cody)

            if (
                stored_username != username
                or stored_device_id != device_id
                or stored_device_key != device_key
                or (
                    previous_target is not None
                    and len(previous_target) == 4
                    and previous_target[3] != cloud_mode
                )
            ):
                print("KeepAlive: IoT settings changed. Updating and resetting " + label)
                WiFi_IoT._last_iot_keep_alive = now
                settings_ok = WiFi_IoT.set_iot(cody, username, device_id, device_key, cloud_mode)
                reset_ok = WiFi_IoT.reset_iot(cody)
                if settings_ok and reset_ok:
                    print("KeepAlive: IoT reset requested " + label)
                return False

        if WiFi_IoT.iot_connected(cody):
            WiFi_IoT._report_iot_state(True, label)
            return True
        WiFi_IoT._report_iot_state(False, label)

        if now - WiFi_IoT._last_iot_keep_alive < float(Trst):
            return False

        WiFi_IoT._last_iot_keep_alive = now
        print("KeepAlive: IoT not connected. Resetting IoT " + label)
        WiFi_IoT.reset_iot(cody)
        return False

    @staticmethod
    def status(cody):
        response = WiFi_IoT._send_fixed(
            cody,
            "CN@@WSTAT@@".ljust(20, "_"),
            "CN@@WSTAT@@",
        )
        if not response or len(response) < 15:
            return None

        try:
            return {
                "wifi": int(response[11:13]),
                "iot": int(response[13:15]),
            }
        except ValueError:
            return None

    @staticmethod
    def wifi_status(cody):
        status = WiFi_IoT.status(cody)
        return None if status is None else status["wifi"]

    @staticmethod
    def iot_status(cody):
        status = WiFi_IoT.status(cody)
        return None if status is None else status["iot"]

    @staticmethod
    def wifi_connected(cody):
        return WiFi_IoT.wifi_status(cody) == 3

    @staticmethod
    def iot_connected(cody):
        return WiFi_IoT.iot_status(cody) == 1

    @staticmethod
    def credential_state(cody, step):
        try:
            step = int(step)
        except (TypeError, ValueError):
            return None

        response = WiFi_IoT._send_fixed(
            cody,
            f"CN@@WCRED@@{step:02d}".ljust(20, "_"),
            "CN@@WCRED@@",
            expected_len=53,
        )
        if not response or len(response) < 53:
            return None
        return response[13:53].rstrip("_")

    @staticmethod
    def get_wifi_ssid(cody):
        return WiFi_IoT.credential_state(cody, 0)

    @staticmethod
    def get_wifi_password(cody):
        return WiFi_IoT.credential_state(cody, 1)

    @staticmethod
    def get_device_id(cody):
        return WiFi_IoT.credential_state(cody, 2)

    @staticmethod
    def get_device_key(cody):
        return WiFi_IoT.credential_state(cody, 3)

    @staticmethod
    def get_username(cody):
        return WiFi_IoT.credential_state(cody, 4)

    @staticmethod
    def get_esp_version(cody):
        return WiFi_IoT.credential_state(cody, 5)

    @staticmethod
    def get_stm_version(cody):
        return WiFi_IoT.credential_state(cody, 6)

    @staticmethod
    def get_lib_version(cody):
        return WiFi_IoT.credential_state(cody, 7)

    @staticmethod
    def _verify_written_value(cody, index, type_code, expected_value):
        actual_value = WiFi_IoT.read(cody, index, type_code)
        if actual_value is None:
            return False

        if type_code == "0":
            return actual_value == int(expected_value)
        if type_code == "1":
            return abs(float(actual_value) - float(expected_value)) <= WiFi_IoT.FLOAT_VERIFY_TOLERANCE
        if type_code == "2":
            return bool(actual_value) == bool(expected_value)

        expected_text = str(expected_value)[:WiFi_IoT.STRING_VERIFY_CHARS]
        actual_text = str(actual_value)[:WiFi_IoT.STRING_VERIFY_CHARS]
        return actual_text == expected_text

    @staticmethod
    def write(cody, index, value_type, value, verify=False):
        type_code = WiFi_IoT.TYPE_CODES.get(str(value_type).strip().lower())
        if type_code is None:
            log("IoT value type must be int, float, bool, or string: " + str(value_type))
            return False

        try:
            index = int(index)
        except (TypeError, ValueError):
            return False
        if index < 0 or index > 3:
            log("IoT index must be 0..3: " + str(index))
            return False

        if type_code == "0":
            expected_value = int(value)
            value = str(expected_value)
        elif type_code == "1":
            expected_value = float(value)
            value = str(expected_value)
        elif type_code == "2":
            expected_value = bool(value)
            value = "true" if expected_value else "false"
        else:
            expected_value = str(value)
            value = str(value)

        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            log("IoT values must be ASCII text.")
            return False
        if len(value) > 40:
            log("IoT values must be 40 characters or fewer.")
            return False

        response = WiFi_IoT._send_variable(
            cody,
            "CN@@IOTW@@",
            f"{type_code}{index}{len(value):02d}{value}",
            "CN@@IOK@@",
        )
        accepted = bool(
            response
            and len(response) >= 12
            and response[9] == type_code
            and response[10] == str(index)
            and response[11] == "1"
        )
        if not accepted:
            return False

        time.sleep(WiFi_IoT.IOT_WRITE_DELAY_SECONDS)

        if not verify:
            return True

        return WiFi_IoT._verify_written_value(cody, index, type_code, expected_value)

    @staticmethod
    def read(cody, index, value_type):
        type_code = WiFi_IoT.TYPE_CODES.get(str(value_type).strip().lower())
        if type_code is None:
            log("IoT value type must be int, float, bool, or string: " + str(value_type))
            return None

        try:
            index = int(index)
        except (TypeError, ValueError):
            return None
        if index < 0 or index > 3:
            log("IoT index must be 0..3: " + str(index))
            return None

        response = WiFi_IoT._send_fixed(
            cody,
            f"CN@@IOTR@@{type_code}{index}".ljust(20, "_"),
            "CN@@IOTR@@",
        )
        if not response or len(response) < 14:
            return None

        try:
            value_len = int(response[12:14])
        except ValueError:
            return None

        value_text = response[14:14 + value_len]
        try:
            if type_code == "0":
                return int(value_text)
            if type_code == "1":
                return float(value_text)
            if type_code == "2":
                return value_text.upper().startswith("T")
            return value_text
        except ValueError:
            return None

    @staticmethod
    def write_int(cody, index, value, verify=False):
        return WiFi_IoT.write(cody, index, "int", int(value), verify=verify)

    @staticmethod
    def write_float(cody, index, value, verify=False):
        return WiFi_IoT.write(cody, index, "float", float(value), verify=verify)

    @staticmethod
    def write_bool(cody, index, value, verify=False):
        return WiFi_IoT.write(cody, index, "bool", bool(value), verify=verify)

    @staticmethod
    def write_string(cody, index, value, verify=False):
        return WiFi_IoT.write(cody, index, "string", str(value), verify=verify)

    @staticmethod
    def read_int(cody, index):
        return WiFi_IoT.read(cody, index, "int")

    @staticmethod
    def read_float(cody, index):
        return WiFi_IoT.read(cody, index, "float")

    @staticmethod
    def read_bool(cody, index):
        return WiFi_IoT.read(cody, index, "bool")

    @staticmethod
    def read_string(cody, index):
        return WiFi_IoT.read(cody, index, "string")


# Keypad functions
class Keypad:
    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def get():
        key = None
        # Implement
        return key


# Sensors
class Sensors:
    def __init__(self):
        raise Exception("This class cannot be instantiated. Use static methods only.")

    @staticmethod
    def temp_sensor_reading():
        temperature = 0.0
        # Implement
        return temperature

    @staticmethod
    def light_sensor_reading():
        light_level = 0.0
        # Implement
        return light_level

    @staticmethod
    def gas_sensor_reading():
        gas_level = 0.0
        # Implement
        return gas_level

    @staticmethod
    def soilhumidity_reading():
        soil_humidity = 0.0
        # Implement
        return soil_humidity

    @staticmethod
    def flow_sensor_reading():
        flow_rate = 0.0
        # Implement
        return flow_rate

    @staticmethod
    def ultrasonic_distance_reading():
        distance = 0.0
        # Implement
        return distance
