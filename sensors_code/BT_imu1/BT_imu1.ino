#include <ArduinoBLE.h>
#include <LSM6DS3.h>
#include <Wire.h>

#define RED_LED LED_RED
#define GREEN_LED LED_GREEN
#define BLUE_LED LED_BLUE

BLEService imuService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic imuDataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 168);
BLEByteCharacteristic controlChar("19B10002-E8F2-537E-4F6C-D104768A1214", BLEWrite);
bool recording = false;

LSM6DS3 myIMU(I2C_MODE, 0x6A);

const int samplesPerBatch = 6;
uint8_t batchedData[168];  // 6 samples * 28 bytes (4 timestamp + 6*4 bytes float)
int bufferIndex = 0;
const unsigned long sampleInterval = 20;
unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(115200);
  imuService.addCharacteristic(controlChar);
  while (!Serial && millis() < 3000);

  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);

  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(BLUE_LED, HIGH);
  digitalWrite(RED_LED, LOW);

  delay(500);

  if (myIMU.begin() != 0) {
    Serial.println("IMU Device error");
  } else {
    Serial.println("Using timestamped float batch mode");
  }

  delay(300);

  if (!BLE.begin()) {
    Serial.println("BLE start failed");
    while (1);
  }

  BLE.setLocalName("IMU_BLE_Device");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuDataCharacteristic);
  BLE.addService(imuService);
  BLE.advertise();
  Serial.println("BLE IMU device advertising");
}

void loop() {
  static unsigned long previousMillis = 0;
  static bool ledState = false;

  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    digitalWrite(RED_LED, HIGH);

    while (central.connected()) {
      unsigned long currentMillis = millis();

      if (currentMillis - previousMillis >= 500) {
        previousMillis = currentMillis;
        ledState = !ledState;
        digitalWrite(BLUE_LED, ledState ? LOW : HIGH);
      }
    if (controlChar.written() && recording == false) {
      if (controlChar.value() == 1) {
        recording = true;
        digitalWrite(GREEN_LED, LOW);  // ON
      }
    }

      unsigned long now = millis();
      if (now - lastSampleTime >= sampleInterval) {
        lastSampleTime = now;

        float aX = myIMU.readFloatAccelX();
        float aY = myIMU.readFloatAccelY();
        float aZ = myIMU.readFloatAccelZ();
        float gX = myIMU.readFloatGyroX();
        float gY = myIMU.readFloatGyroY();
        float gZ = myIMU.readFloatGyroZ();

        bool valid = isfinite(aX) && isfinite(aY) && isfinite(aZ) &&
                     isfinite(gX) && isfinite(gY) && isfinite(gZ);
        if (!valid) {
          Serial.println("Invalid IMU reading, skipping");
          continue;
        }

        int offset = bufferIndex * 28;

        uint32_t ts = millis();
        memcpy(&batchedData[offset], &ts, 4);  // store timestamp (4 bytes)

        float values[6] = {aX, aY, aZ, gX, gY, gZ};
        memcpy(&batchedData[offset + 4], values, sizeof(values));  // store 6 floats

        bufferIndex++;

        if (bufferIndex == samplesPerBatch) {
          bool sent = imuDataCharacteristic.writeValue(batchedData, sizeof(batchedData));
          Serial.println(sent ? "Batch sent" : "BLE write failed");
          delay(1);  // Small throttle to avoid BLE flooding


          for (int i = 0; i < samplesPerBatch; i++) {
            int off = i * 28;
            uint32_t t;
            memcpy(&t, &batchedData[off], 4);
            Serial.print("t="); Serial.print(t); Serial.print("ms | ");
            for (int j = 0; j < 6; j++) {
              float val;
              memcpy(&val, &batchedData[off + 4 + j * 4], 4);
              Serial.print(val, 3);
              Serial.print(j < 5 ? ", " : "\n");
            }
          }

          bufferIndex = 0;
        }
      }
    }
    recording = false;
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }

  digitalWrite(RED_LED, LOW);
  digitalWrite(BLUE_LED, HIGH);
  digitalWrite(GREEN_LED, HIGH);
}
