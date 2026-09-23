#include <Arduino.h>
#include <stdlib.h>
#include <Wire.h>
#include <avr/wdt.h>
// #include "CodyNick/I2A_display_v2.h"
// #include "CodyNick/I2A_Buzzer_joystick_v1_0.h"
#include <I2A_display_v2.h>
#include <I2A_Buzzer_joystick_v1_0.h>
#include <I2A_Buzzer_V1.h>
#include <I2A_DS18B20_v1_1.h>
#include <I2A_joy_mat_v1_0.h>
#include <I2A_PIR_v1_0.h>
#include <I2A_RFID_v1_2.h>
#include <I2A_RGB_MAT_v1.h>
#include <I2A_Soil_Moisture_v1_1.h>
#include <I2A_WiFi_IoT_v2.h>

// ---------- Version ----------
const char CODYPI_VERSION[] = "1.19.4";

// ---------- Config ----------
const uint8_t PKT_LEN   = 20; // 4 bytes header + 16 bytes payload
const uint8_t HEADER_LEN = 4;

// IDENTIFY prefix (first 12 bytes): "CN@@IDENTIFY"
const uint8_t IDENTIFY_PREFIX[12] = {
  'C','N','@','@','I','D','E','N','T','I','F','Y'
};

// IDENTIFY response: "CN@@CJP-Neo" + padding zeros to 20 bytes
const uint8_t IDENTIFY_RESPONSE[PKT_LEN] = {
  'C','N','@','@','C','J','P','-','N','e','o',
  0,0,0,0,0,0,0,0,0
};

uint64_t ultrasonicTimer[2] = {0, 0};
float ultrasonicDistance[2] = {0.0, 0.0};
const uint8_t ULTRASONIC_I2C_ADDRESS[2] = {14, 61};
int cjpJoyCenterX = 512;
int cjpJoyCenterY = 512;
const int CJP_JOY_DEADZONE = 160;

// ---------- Prototypes ----------
void handleSerialPackets();
uint32_t parseHexColor(const char *colorStr);
void writeResponse(const uint8_t *resp);
void writeFixedTextResponse(const char *header, uint8_t headerLen, const char *value, uint8_t valueLen);
void writeJoystickResponse(uint8_t joystickIndex);
void updateUltrasonicDistance(uint8_t ultrasonicIndex);
void writeWifiOkResponse(char field, bool ok);
void writeIotWriteResponse(char typeChar, char indexChar, bool ok);
void writeIotReadResponse(char typeChar, char indexChar, const char *value);
bool handleWifiConfig(char field, const char *value);
bool handleIotWrite(char typeChar, uint8_t index, const char *value);
void calibrateCjpJoystick();
uint8_t readCalibratedCjpJoystick();

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);       // Command channel

  Wire_Begin();               // Shared I2C init for CodyNick chain gadgets
  init_Soil_Moisture(0);      // Stand-alone soil moisture sensor init (index 0)
  seven_segment_init_V2(0);   // Stand-alone 7-seg init (index 0)
  seven_segment_init_V2(2);   // UltraSeg 7-seg init (index 2)
  RGB_LED_MAT_INIT(1);        // CodyNick RGB matrix init (index 1)
  buzzer_initial(0);          // CodyJoy Pro sound maker init (index 0)

  // Joystick init
  // delay(2000);
  joystick_initial(0);        // Stand-alone joystick
  joystick_initial(5);
  calibrateCjpJoystick();
}

// ---------- Main loop ----------
void loop() {
  handleSerialPackets();
}

// ---------- Stream-based serial handler ----------
void handleSerialPackets() {
  static uint8_t rxBuf[PKT_LEN];
  static char ledTextBuf[50];
  static char wifiTextBuf[41];
  static char iotTextBuf[41];

  enum ParserState {
    SEEK_HEADER,
    READ_PAYLOAD,
    READ_LED_TEXT_SPEED,
    READ_LED_TEXT_LEN_TENS,
    READ_LED_TEXT_LEN_ONES,
    READ_LED_TEXT_BODY,
    READ_WIFI_FIELD,
    READ_WIFI_LEN_TENS,
    READ_WIFI_LEN_ONES,
    READ_WIFI_BODY,
    READ_IOTW_TYPE,
    READ_IOTW_INDEX,
    READ_IOTW_LEN_TENS,
    READ_IOTW_LEN_ONES,
    READ_IOTW_BODY
  };
  static ParserState state = SEEK_HEADER;

  static uint8_t headerIndex  = 0;  // match index in "CN@@"
  static uint8_t payloadIndex = 0;  // position in rxBuf during payload read
  static uint8_t ledTextSpeed = 0;
  static uint8_t ledTextLen = 0;
  static uint8_t ledTextIndex = 0;
  static char wifiField = 0;
  static uint8_t wifiTextLen = 0;
  static uint8_t wifiTextIndex = 0;
  static char iotTypeChar = 0;
  static char iotIndexChar = 0;
  static uint8_t iotTextLen = 0;
  static uint8_t iotTextIndex = 0;

  while (Serial.available() > 0) {
    uint8_t b = (uint8_t)Serial.read();

    // -------- SEEK_HEADER state --------
    if (state == SEEK_HEADER) {
      const uint8_t HEADER[HEADER_LEN] = { 'C','N','@','@' };

      if (b == HEADER[headerIndex]) {
        headerIndex++;

        if (headerIndex == HEADER_LEN) {
          // Full header matched → put it in rxBuf[0..3]
          for (uint8_t i = 0; i < HEADER_LEN; i++) {
            rxBuf[i] = HEADER[i];
          }
          payloadIndex = HEADER_LEN;   // next bytes go to payload
          state = READ_PAYLOAD;
        }
      } else {
        // If this byte could be the start again, keep headerIndex at 1
        if (b == 'C') {
          headerIndex = 1;
        } else {
          headerIndex = 0;
        }
      }
    }

    // -------- READ_PAYLOAD state --------
    else if (state == READ_PAYLOAD) {
      rxBuf[payloadIndex++] = b;

      // Variable-length LED text command prefix: "CN@@LTXT@@"
      if (payloadIndex == 10 &&
          rxBuf[4] == 'L' && rxBuf[5] == 'T' &&
          rxBuf[6] == 'X' && rxBuf[7] == 'T' &&
          rxBuf[8] == '@' && rxBuf[9] == '@') {
        state = READ_LED_TEXT_SPEED;
        continue;
      }

      // Variable-length WiFi config command prefix: "CN@@WIFI@@"
      if (payloadIndex == 10 &&
          rxBuf[4] == 'W' && rxBuf[5] == 'I' &&
          rxBuf[6] == 'F' && rxBuf[7] == 'I' &&
          rxBuf[8] == '@' && rxBuf[9] == '@') {
        state = READ_WIFI_FIELD;
        continue;
      }

      // Variable-length IoT write command prefix: "CN@@IOTW@@"
      if (payloadIndex == 10 &&
          rxBuf[4] == 'I' && rxBuf[5] == 'O' &&
          rxBuf[6] == 'T' && rxBuf[7] == 'W' &&
          rxBuf[8] == '@' && rxBuf[9] == '@') {
        state = READ_IOTW_TYPE;
        continue;
      }

      if (payloadIndex >= PKT_LEN) {
        // We now have a full 20-byte frame in rxBuf
        state = SEEK_HEADER;
        headerIndex = 0;
        payloadIndex = 0;

        // ------------- COMMAND HANDLING ----------------
        // rxBuf[0..3] = "CN@@"
        // rxBuf[4..]  = payload

        // -------- IDENTIFY COMMAND --------
        bool isIdentify = true;
        for (uint8_t i = 0; i < 12; i++) {
          if (rxBuf[i] != IDENTIFY_PREFIX[i]) {
            isIdentify = false;
            break;
          }
        }

        if (isIdentify) {
          writeResponse(IDENTIFY_RESPONSE);
          continue;
        }

        // -------- 7SEG COMMAND --------
        //
        // Pattern: CN@@7SEG@@<NN><num><pad> (total 20 bytes)
        // Indexing:
        //   0..3  = 'C','N','@','@'
        //   4..9  = '7','S','E','G','@','@'
        //   10..11 = device index, ASCII digits
        //   12..17 = ASCII number (may include '-', '.')
        //   18..19 = padding, ignored
        //
        bool is7Seg =
          (rxBuf[4] == '7' && rxBuf[5] == 'S' &&
           rxBuf[6] == 'E' && rxBuf[7] == 'G' &&
           rxBuf[8] == '@' && rxBuf[9] == '@');

        if (is7Seg) {
          if (rxBuf[10] >= '0' && rxBuf[10] <= '9' &&
              rxBuf[11] >= '0' && rxBuf[11] <= '9') {
            uint8_t displayIndex = (rxBuf[10] - '0') * 10 + (rxBuf[11] - '0');

            if (displayIndex == 0 || displayIndex == 2) {
              char numStr[7];  // 6 chars + '\0'
              for (uint8_t i = 0; i < 6; i++) {
                numStr[i] = (char)rxBuf[12 + i];
              }
              numStr[6] = '\0';

              float val = atof(numStr);
              write_to_sevensegment_V2(val, displayIndex);
            }
          }
          continue;
        }

        // -------- RGB MATRIX SET LED COMMAND --------
        //
        // Pattern: CN@@RGB@@<NN><#RRGGBB><pad> (total 20 bytes)
        // Example: CN@@RGB@@15#4FD300
        //
        bool isRgbSet =
          (rxBuf[4] == 'R' && rxBuf[5] == 'G' &&
           rxBuf[6] == 'B' && rxBuf[7] == '@' &&
           rxBuf[8] == '@');

        if (isRgbSet) {
          char ledStr[3];
          ledStr[0] = (char)rxBuf[9];
          ledStr[1] = (char)rxBuf[10];
          ledStr[2] = '\0';

          uint8_t ledIndex = (uint8_t)atoi(ledStr);
          if (ledIndex <= 15 && rxBuf[11] == '#') {
            char colorStr[8];
            for (uint8_t i = 0; i < 7; i++) {
              colorStr[i] = (char)rxBuf[11 + i];
            }
            colorStr[7] = '\0';

            SET_RGB_Mat_X_CC_24bit(1, ledIndex, parseHexColor(colorStr));
          }
          continue;
        }

        // -------- RGB MATRIX CLEAR COMMAND --------
        //
        // Pattern: CN@@RGBCLR@@<pad> (total 20 bytes)
        //
        bool isRgbClear =
          (rxBuf[4] == 'R' && rxBuf[5] == 'G' &&
           rxBuf[6] == 'B' && rxBuf[7] == 'C' &&
           rxBuf[8] == 'L' && rxBuf[9] == 'R' &&
           rxBuf[10] == '@' && rxBuf[11] == '@');

        if (isRgbClear) {
          Clear_All_RGB_Mat(1);
          continue;
        }

        // -------- LED MATRIX PIXEL COMMAND --------
        //
        // Pattern: CN@@LPX@@<x><y><state><pad> (total 20 bytes)
        // Example: CN@@LPX@@341________
        //
        bool isLedPixel =
          (rxBuf[4] == 'L' && rxBuf[5] == 'P' &&
           rxBuf[6] == 'X' && rxBuf[7] == '@' &&
           rxBuf[8] == '@');

        if (isLedPixel) {
          if (rxBuf[9] >= '0' && rxBuf[9] <= '7' &&
              rxBuf[10] >= '0' && rxBuf[10] <= '7' &&
              (rxBuf[11] == '0' || rxBuf[11] == '1')) {
            uint8_t x = rxBuf[9] - '0';
            uint8_t y = rxBuf[10] - '0';
            uint8_t stateValue = rxBuf[11] - '0';
            set_dot_mat_point(x, y, stateValue, 0);
          }
          continue;
        }

        // -------- LED MATRIX CLEAR COMMAND --------
        //
        // Pattern: CN@@LCLR@@<pad> (total 20 bytes)
        //
        bool isLedClear =
          (rxBuf[4] == 'L' && rxBuf[5] == 'C' &&
           rxBuf[6] == 'L' && rxBuf[7] == 'R' &&
           rxBuf[8] == '@' && rxBuf[9] == '@');

        if (isLedClear) {
          dot_matrix_clear_all(0);
          continue;
        }

        // -------- SOUND MAKER COMMAND --------
        //
        // Pattern: CN@@BUZ@@<freq><duration><pad> (total 20 bytes)
        // Example: CN@@BUZ@@009300300__
        //   freq     = bytes 9..12  (rounded Hz, 0030..5000)
        //   duration = bytes 13..17 (milliseconds)
        //
        bool isBuzzer =
          (rxBuf[4] == 'B' && rxBuf[5] == 'U' &&
           rxBuf[6] == 'Z' && rxBuf[7] == '@' &&
           rxBuf[8] == '@');

        if (isBuzzer) {
          char freqStr[5];
          for (uint8_t i = 0; i < 4; i++) {
            freqStr[i] = (char)rxBuf[9 + i];
          }
          freqStr[4] = '\0';

          char durationStr[6];
          for (uint8_t i = 0; i < 5; i++) {
            durationStr[i] = (char)rxBuf[13 + i];
          }
          durationStr[5] = '\0';

          uint16_t freq = (uint16_t)atoi(freqStr);
          uint16_t duration = (uint16_t)atoi(durationStr);

          if (freq >= 30 && freq <= 5000 && duration > 0) {
            set_buzzer_tone(duration, freq, 0);
          }
          continue;
        }

        // -------- MOTION DETECTION COMMAND --------
        //
        // Pattern: CN@@PIR@@<pad> (total 20 bytes)
        // Response: CN@@PIR@@1__________ or CN@@PIR@@0__________
        //
        bool isPir =
          (rxBuf[4] == 'P' && rxBuf[5] == 'I' &&
           rxBuf[6] == 'R' && rxBuf[7] == '@' &&
           rxBuf[8] == '@');

        if (isPir) {
          uint8_t resp[PKT_LEN] = {
            'C','N','@','@',
            'P','I','R','@','@',
            '0','_','_','_','_','_','_','_','_','_','_'
          };

          resp[9] = Detect_Motion() ? '1' : '0';
          writeResponse(resp);
          continue;
        }

        // -------- TEMPERATURE SENSOR COMMAND --------
        //
        // Pattern: CN@@TEMP@@<pad> (total 20 bytes)
        // Response: CN@@TEMP@@<value><pad>
        //
        bool isTemperature =
          (rxBuf[4] == 'T' && rxBuf[5] == 'E' &&
           rxBuf[6] == 'M' && rxBuf[7] == 'P' &&
           rxBuf[8] == '@' && rxBuf[9] == '@');

        if (isTemperature) {
          char tempStr[11];
          String tempValue = String(GET_TEMPERTURE_SENSOR_VALUE(0), 1);
          tempValue.toCharArray(tempStr, sizeof(tempStr));

          uint8_t resp[PKT_LEN] = {
            'C','N','@','@',
            'T','E','M','P','@','@',
            '_','_','_','_','_','_','_','_','_','_'
          };

          for (uint8_t i = 0; i < 10 && tempStr[i] != '\0'; i++) {
            resp[10 + i] = tempStr[i];
          }

          writeResponse(resp);
          continue;
        }

        // -------- SOIL MOISTURE SENSOR COMMAND --------
        //
        // Pattern: CN@@SOIL@@<pad> (total 20 bytes)
        // Response: CN@@SOIL@@<value><pad>
        //
        bool isSoilMoisture =
          (rxBuf[4] == 'S' && rxBuf[5] == 'O' &&
           rxBuf[6] == 'I' && rxBuf[7] == 'L' &&
           rxBuf[8] == '@' && rxBuf[9] == '@');

        if (isSoilMoisture) {
          char soilStr[11];
          String soilValue = String(get_soil_moisture_value(0), 1);
          soilValue.toCharArray(soilStr, sizeof(soilStr));

          uint8_t resp[PKT_LEN] = {
            'C','N','@','@',
            'S','O','I','L','@','@',
            '_','_','_','_','_','_','_','_','_','_'
          };

          for (uint8_t i = 0; i < 10 && soilStr[i] != '\0'; i++) {
            resp[10 + i] = soilStr[i];
          }

          writeResponse(resp);
          continue;
        }

        // -------- RFID READER COMMAND --------
        //
        // Pattern: CN@@RFID@@<pad> (total 20 bytes)
        // Response: CN@@RFID@@<8 hex UID chars><pad>
        //
        bool isRfid =
          (rxBuf[4] == 'R' && rxBuf[5] == 'F' &&
           rxBuf[6] == 'I' && rxBuf[7] == 'D' &&
           rxBuf[8] == '@' && rxBuf[9] == '@');

        if (isRfid) {
          GET_RFID_UID_DATA(0);

          char uidStr[9];
          snprintf(uidStr, sizeof(uidStr), "%08lX", RFID_UID);

          uint8_t resp[PKT_LEN] = {
            'C','N','@','@',
            'R','F','I','D','@','@',
            '_','_','_','_','_','_','_','_','_','_'
          };

          for (uint8_t i = 0; i < 8; i++) {
            resp[10 + i] = uidStr[i];
          }

          writeResponse(resp);
          continue;
        }

        // -------- ULTRASONIC SENSOR COMMAND --------
        //
        // Pattern: CN@@ULTRA@@<NN><pad> (total 20 bytes)
        // Response: CN@@ULTRA@@<NN><value><pad>
        //
        bool isUltrasonic =
          (rxBuf[4] == 'U' && rxBuf[5] == 'L' &&
           rxBuf[6] == 'T' && rxBuf[7] == 'R' &&
           rxBuf[8] == 'A' && rxBuf[9] == '@' &&
           rxBuf[10] == '@');

        if (isUltrasonic) {
          if (rxBuf[11] >= '0' && rxBuf[11] <= '9' &&
              rxBuf[12] >= '0' && rxBuf[12] <= '9') {
            uint8_t ultrasonicIndex = (rxBuf[11] - '0') * 10 + (rxBuf[12] - '0');

            if (ultrasonicIndex <= 1) {
              updateUltrasonicDistance(ultrasonicIndex);

              char distanceStr[8];
              float distanceCm = ultrasonicDistance[ultrasonicIndex];
              if (ultrasonicIndex == 1) {
                distanceCm = distanceCm / 10.0;
              }
              String distanceValue = String(distanceCm, 1);
              distanceValue.toCharArray(distanceStr, sizeof(distanceStr));

              uint8_t resp[PKT_LEN] = {
                'C','N','@','@',
                'U','L','T','R','A','@','@',
                '0','0',
                '_','_','_','_','_','_','_'
              };

              resp[11] = '0' + (ultrasonicIndex / 10);
              resp[12] = '0' + (ultrasonicIndex % 10);

              for (uint8_t i = 0; i < 7 && distanceStr[i] != '\0'; i++) {
                resp[13 + i] = distanceStr[i];
              }

              writeResponse(resp);
            }
          }
          continue;
        }

        // -------- WIFI/IOT STATUS COMMAND --------
        //
        // Pattern: CN@@WSTAT@@<pad> (total 20 bytes)
        // Response: CN@@WSTAT@@<wifi><iot><pad>
        //
        bool isWifiStatus =
          (rxBuf[4] == 'W' && rxBuf[5] == 'S' &&
           rxBuf[6] == 'T' && rxBuf[7] == 'A' &&
           rxBuf[8] == 'T' && rxBuf[9] == '@' &&
           rxBuf[10] == '@');

        if (isWifiStatus) {
          uint8_t resp[PKT_LEN] = {
            'C','N','@','@',
            'W','S','T','A','T','@','@',
            '0','0','0','0',
            '_','_','_','_','_'
          };

          uint8_t wifiStatus = Get_Wifi_Status();
          uint8_t iotStatus = Get_IoT_Status();
          resp[11] = '0' + (wifiStatus / 10);
          resp[12] = '0' + (wifiStatus % 10);
          resp[13] = '0' + (iotStatus / 10);
          resp[14] = '0' + (iotStatus % 10);
          writeResponse(resp);
          continue;
        }

        // -------- WIFI CREDENTIAL STATE COMMAND --------
        //
        // Pattern: CN@@WCRED@@<NN><pad> (total 20 bytes)
        // Response: CN@@WCRED@@<NN><40 chars padded with underscores>
        //
        bool isWifiCred =
          (rxBuf[4] == 'W' && rxBuf[5] == 'C' &&
           rxBuf[6] == 'R' && rxBuf[7] == 'E' &&
           rxBuf[8] == 'D' && rxBuf[9] == '@' &&
           rxBuf[10] == '@');

        if (isWifiCred) {
          if (rxBuf[11] >= '0' && rxBuf[11] <= '9' &&
              rxBuf[12] >= '0' && rxBuf[12] <= '9') {
            uint8_t credType = (rxBuf[11] - '0') * 10 + (rxBuf[12] - '0');
            String cred = Get_Cred_State(credType);

            char header[14] = {
              'C','N','@','@',
              'W','C','R','E','D','@','@',
              (char)('0' + (credType / 10)),
              (char)('0' + (credType % 10)),
              '\0'
            };
            writeFixedTextResponse(header, 13, cred.c_str(), 40);
          }
          continue;
        }

        // -------- WIFI/IOT RESET COMMAND --------
        //
        // Pattern: CN@@WRST@@<E/W/D><pad> (total 20 bytes)
        // Response: CN@@WOK@@<E/W/D>1<pad>
        //   E = restart WiFi/IoT interface controller
        //   W = request WiFi reconnect/reset
        //   D = request IoT device reconnect/reset
        //
        bool isWifiReset =
          (rxBuf[4] == 'W' && rxBuf[5] == 'R' &&
           rxBuf[6] == 'S' && rxBuf[7] == 'T' &&
           rxBuf[8] == '@' && rxBuf[9] == '@');

        if (isWifiReset) {
          char resetType = (char)rxBuf[10];
          bool handled = true;

          if (resetType == 'E') {
            IoT_ESP_Restart();
          } else if (resetType == 'W') {
            IoT_Wifi_Reset();
          } else if (resetType == 'D') {
            IoT_Device_Reset();
          } else {
            handled = false;
          }

          writeWifiOkResponse(resetType, handled);
          continue;
        }

        // -------- IOT READ COMMAND --------
        //
        // Pattern: CN@@IOTR@@<type><index><pad> (total 20 bytes)
        // Response: CN@@IOTR@@<type><index><len><value><pad>
        //
        bool isIotRead =
          (rxBuf[4] == 'I' && rxBuf[5] == 'O' &&
           rxBuf[6] == 'T' && rxBuf[7] == 'R' &&
           rxBuf[8] == '@' && rxBuf[9] == '@');

        if (isIotRead) {
          char typeChar = (char)rxBuf[10];
          char indexChar = (char)rxBuf[11];
          if (typeChar >= '0' && typeChar <= '3' &&
              indexChar >= '0' && indexChar <= '3') {
            uint8_t index = indexChar - '0';
            char valueStr[41];
            valueStr[0] = '\0';

            if (typeChar == '0') {
              String value = String(Get_IoT_Int(index));
              value.toCharArray(valueStr, sizeof(valueStr));
            } else if (typeChar == '1') {
              String value = String(Get_IoT_Float(index), 2);
              value.toCharArray(valueStr, sizeof(valueStr));
            } else if (typeChar == '2') {
              valueStr[0] = Get_IoT_Bool(index) ? 'T' : 'F';
              valueStr[1] = '\0';
            } else if (typeChar == '3') {
              String value = Get_IoT_String(index);
              value.toCharArray(valueStr, sizeof(valueStr));
            }

            writeIotReadResponse(typeChar, indexChar, valueStr);
          }
          continue;
        }

        // -------- JOYSTICK COMMAND --------
        //
        // Pattern: CN@@JOY@@<NN><pad> (total 20 bytes)
        // Example: CN@@JOY@@05_________
        // Response: CN@@JOY@@05ULC______ (always 20 bytes)
        //
        bool isJoystick =
          (rxBuf[4] == 'J' && rxBuf[5] == 'O' &&
           rxBuf[6] == 'Y' && rxBuf[7] == '@' &&
           rxBuf[8] == '@');

        if (isJoystick) {
          if (rxBuf[9] >= '0' && rxBuf[9] <= '9' &&
              rxBuf[10] >= '0' && rxBuf[10] <= '9') {
            uint8_t joystickIndex = (rxBuf[9] - '0') * 10 + (rxBuf[10] - '0');
            if (joystickIndex <= 5) {
              writeJoystickResponse(joystickIndex);
            }
          }
          continue;
        }

        // -------- Other CN@@ commands (future) --------
        // Add more handlers here by checking rxBuf[4..] pattern.
      }
    }

    else if (state == READ_LED_TEXT_SPEED) {
      if (b >= '0' && b <= '2') {
        ledTextSpeed = b - '0';
        state = READ_LED_TEXT_LEN_TENS;
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_LED_TEXT_LEN_TENS) {
      if (b >= '0' && b <= '4') {
        ledTextLen = (b - '0') * 10;
        state = READ_LED_TEXT_LEN_ONES;
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_LED_TEXT_LEN_ONES) {
      if (b >= '0' && b <= '9') {
        ledTextLen += b - '0';
        if (ledTextLen > 49) {
          state = SEEK_HEADER;
          headerIndex = 0;
        } else if (ledTextLen == 0) {
          ledTextBuf[0] = '\0';
          set_dot_mat_text(String(ledTextBuf), ledTextSpeed, 0);
          state = SEEK_HEADER;
          headerIndex = 0;
        } else {
          ledTextIndex = 0;
          state = READ_LED_TEXT_BODY;
        }
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_LED_TEXT_BODY) {
      ledTextBuf[ledTextIndex++] = (char)b;
      if (ledTextIndex >= ledTextLen) {
        ledTextBuf[ledTextIndex] = '\0';
        set_dot_mat_text(String(ledTextBuf), ledTextSpeed, 0);
        state = SEEK_HEADER;
        headerIndex = 0;
        payloadIndex = 0;
        ledTextIndex = 0;
      }
    }

    else if (state == READ_WIFI_FIELD) {
      if (b == 'S' || b == 'P' || b == 'M' || b == 'U' || b == 'D' || b == 'K') {
        wifiField = (char)b;
        state = READ_WIFI_LEN_TENS;
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_WIFI_LEN_TENS) {
      if (b >= '0' && b <= '4') {
        wifiTextLen = (b - '0') * 10;
        state = READ_WIFI_LEN_ONES;
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_WIFI_LEN_ONES) {
      if (b >= '0' && b <= '9') {
        wifiTextLen += b - '0';
        if (wifiTextLen > 40) {
          state = SEEK_HEADER;
          headerIndex = 0;
        } else {
          wifiTextIndex = 0;
          state = READ_WIFI_BODY;
        }
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_WIFI_BODY) {
      if (wifiTextIndex < sizeof(wifiTextBuf) - 1) {
        wifiTextBuf[wifiTextIndex++] = (char)b;
      }
      if (wifiTextIndex >= wifiTextLen) {
        wifiTextBuf[wifiTextIndex] = '\0';
        bool ok = handleWifiConfig(wifiField, wifiTextBuf);
        writeWifiOkResponse(wifiField, ok);
        state = SEEK_HEADER;
        headerIndex = 0;
        payloadIndex = 0;
        wifiTextIndex = 0;
      }
    }

    else if (state == READ_IOTW_TYPE) {
      if (b >= '0' && b <= '3') {
        iotTypeChar = (char)b;
        state = READ_IOTW_INDEX;
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_IOTW_INDEX) {
      if (b >= '0' && b <= '3') {
        iotIndexChar = (char)b;
        state = READ_IOTW_LEN_TENS;
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_IOTW_LEN_TENS) {
      if (b >= '0' && b <= '4') {
        iotTextLen = (b - '0') * 10;
        state = READ_IOTW_LEN_ONES;
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_IOTW_LEN_ONES) {
      if (b >= '0' && b <= '9') {
        iotTextLen += b - '0';
        if (iotTextLen > 40) {
          state = SEEK_HEADER;
          headerIndex = 0;
        } else {
          iotTextIndex = 0;
          state = READ_IOTW_BODY;
        }
      } else {
        state = SEEK_HEADER;
        headerIndex = 0;
      }
    }

    else if (state == READ_IOTW_BODY) {
      if (iotTextIndex < sizeof(iotTextBuf) - 1) {
        iotTextBuf[iotTextIndex++] = (char)b;
      }
      if (iotTextIndex >= iotTextLen) {
        iotTextBuf[iotTextIndex] = '\0';
        bool ok = handleIotWrite(iotTypeChar, iotIndexChar - '0', iotTextBuf);
        writeIotWriteResponse(iotTypeChar, iotIndexChar, ok);
        state = SEEK_HEADER;
        headerIndex = 0;
        payloadIndex = 0;
        iotTextIndex = 0;
      }
    }
  }
}

uint32_t parseHexColor(const char *colorStr) {
  if (colorStr == NULL || colorStr[0] != '#') {
    return 0;
  }

  uint32_t color = 0;
  for (uint8_t i = 1; i <= 6; i++) {
    char c = colorStr[i];
    uint8_t value;

    if (c >= '0' && c <= '9') {
      value = c - '0';
    } else if (c >= 'A' && c <= 'F') {
      value = c - 'A' + 10;
    } else if (c >= 'a' && c <= 'f') {
      value = c - 'a' + 10;
    } else {
      return 0;
    }

    color = (color << 4) | value;
  }

  return color;
}

void writeResponse(const uint8_t *resp) {
  Serial.write(resp, PKT_LEN);
  Serial.write('\n');
}

void writeFixedTextResponse(const char *header, uint8_t headerLen, const char *value, uint8_t valueLen) {
  Serial.write((const uint8_t *)header, headerLen);

  uint8_t i = 0;
  if (value != NULL) {
    for (; i < valueLen && value[i] != '\0'; i++) {
      Serial.write((uint8_t)value[i]);
    }
  }

  for (; i < valueLen; i++) {
    Serial.write((uint8_t)'_');
  }

  Serial.write('\n');
}

void writeJoystickResponse(uint8_t joystickIndex) {
  if (joystickIndex == 5) {
    direction[joystickIndex] = readCalibratedCjpJoystick();
  } else {
    Read_joystick_value(joystickIndex);
  }

  uint8_t resp[PKT_LEN] = {
    'C','N','@','@','J','O','Y','@','@',
    '0','0',
    '_','_','_','_','_','_','_','_','_'
  };

  resp[9] = '0' + (joystickIndex / 10);
  resp[10] = '0' + (joystickIndex % 10);

  uint8_t stateIndex = 11;
  uint8_t d = direction[joystickIndex];

  uint8_t xBits = d & (DIRX | DIRXP | SPEEDX);
  if (xBits == (DIRX | SPEEDX)) {
    resp[stateIndex++] = 'U';
  } else if (xBits == (DIRX | SPEEDX | DIRXP)) {
    resp[stateIndex++] = 'D';
  }

  uint8_t yBits = d & (DIRY | DIRYP | SPEEDY);
  if (yBits == (DIRY | SPEEDY | DIRYP)) {
    resp[stateIndex++] = 'L';
  } else if (yBits == (DIRY | SPEEDY)) {
    resp[stateIndex++] = 'R';
  }

  if ((d & CLICK) == CLICK) {
    resp[stateIndex++] = 'C';
  }

  if (stateIndex == 11) {
    resp[stateIndex++] = 'N';
  }

  writeResponse(resp);
}

void updateUltrasonicDistance(uint8_t ultrasonicIndex) {
  if (ultrasonicIndex > 1) {
    return;
  }

  if (millis() - ultrasonicTimer[ultrasonicIndex] > 500) {
    wdt_enable(WDTO_2S);
    ultrasonicTimer[ultrasonicIndex] = millis();
    Wire.requestFrom(ULTRASONIC_I2C_ADDRESS[ultrasonicIndex], (uint8_t)2);

    if (Wire.available() >= 2) {
      uint8_t lowByte = Wire.read();
      uint8_t highByte = Wire.read();
      ultrasonicDistance[ultrasonicIndex] = lowByte + highByte * 256.0;
    }

    wdt_disable();
  }
}

void writeWifiOkResponse(char field, bool ok) {
  uint8_t resp[PKT_LEN] = {
    'C','N','@','@',
    'W','O','K','@','@',
    'X','0',
    '_','_','_','_','_','_','_','_','_'
  };
  resp[9] = field;
  resp[10] = ok ? '1' : '0';
  writeResponse(resp);
}

void writeIotWriteResponse(char typeChar, char indexChar, bool ok) {
  uint8_t resp[PKT_LEN] = {
    'C','N','@','@',
    'I','O','K','@','@',
    '0','0','0',
    '_','_','_','_','_','_','_','_'
  };
  resp[9] = typeChar;
  resp[10] = indexChar;
  resp[11] = ok ? '1' : '0';
  writeResponse(resp);
}

void writeIotReadResponse(char typeChar, char indexChar, const char *value) {
  uint8_t resp[PKT_LEN] = {
    'C','N','@','@',
    'I','O','T','R','@','@',
    '0','0','0','0',
    '_','_','_','_','_','_'
  };

  uint8_t len = 0;
  if (value != NULL) {
    len = strlen(value);
    if (len > 6) {
      len = 6;
    }
  }

  resp[10] = typeChar;
  resp[11] = indexChar;
  resp[12] = '0' + (len / 10);
  resp[13] = '0' + (len % 10);

  for (uint8_t i = 0; i < len; i++) {
    resp[14 + i] = value[i];
  }

  writeResponse(resp);
}

bool handleWifiConfig(char field, const char *value) {
  if (value == NULL) {
    return false;
  }

  switch (field) {
    case 'S':
      return Set_Wifi_SSID(value);
    case 'P':
      return Set_Wifi_PASS(value);
    case 'M':
      return Set_IoT_CloudMode((char)atoi(value));
    case 'U':
      return Set_IoT_UserName(value);
    case 'D':
      return Set_IoT_DeviceID(value);
    case 'K':
      return Set_IoT_DeviceKey(value);
    default:
      return false;
  }
}

bool handleIotWrite(char typeChar, uint8_t index, const char *value) {
  if (typeChar < '0' || typeChar > '3' || index > 3 || value == NULL) {
    return false;
  }

  Set_IoT_Data(typeChar - '0', index, value);
  return true;
}

void calibrateCjpJoystick() {
  long sumX = 0;
  long sumY = 0;
  const uint8_t samples = 20;

  for (uint8_t i = 0; i < samples; i++) {
    sumX += analogRead(VRY_PIN);
    sumY += analogRead(VRX_PIN);
    delay(5);
  }

  cjpJoyCenterX = sumX / samples;
  cjpJoyCenterY = sumY / samples;
}

uint8_t readCalibratedCjpJoystick() {
  uint8_t d = 0;
  int x = analogRead(VRY_PIN);
  int y = analogRead(VRX_PIN);

  if (x < cjpJoyCenterX - CJP_JOY_DEADZONE) {
    d |= DIRX | SPEEDX;
  } else if (x > cjpJoyCenterX + CJP_JOY_DEADZONE) {
    d |= DIRX | SPEEDX | DIRXP;
  }

  if (y < cjpJoyCenterY - CJP_JOY_DEADZONE) {
    d |= DIRY | SPEEDY | DIRYP;
  } else if (y > cjpJoyCenterY + CJP_JOY_DEADZONE) {
    d |= DIRY | SPEEDY;
  }

  if (digitalRead(SW_PIN) == 0) {
    d |= CLICK;
  }

  return d;
}
