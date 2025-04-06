// BLELogger.ino (Arduino) - IMU Batching with Flattened Float Buffer

#include <ArduinoBLE.h>
#include <LSM6DS3.h>
#include <Wire.h>

#define RED_LED LED_RED
#define GREEN_LED LED_GREEN
#define BLUE_LED LED_BLUE

BLEService imuService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic imuDataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 144);

LSM6DS3 myIMU(I2C_MODE, 0x6A);

const int samplesPerBatch = 6;
float batchedData[samplesPerBatch * 6];
int bufferIndex = 0;
const unsigned long sampleInterval = 20;
unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(9600);
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
    Serial.println("Using float batch mode");
  }

  delay(300);

  if (!BLE.begin()) {
    while (1);
  }

  BLE.setLocalName("IMU_BLE_Device");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuDataCharacteristic);
  BLE.addService(imuService);
  BLE.advertise();
}

void loop() {
  static unsigned long previousMillis = 0;
  static bool ledState = false;

  BLEDevice central = BLE.central();

  if (central) {
    digitalWrite(RED_LED, HIGH);

    while (central.connected()) {
      unsigned long currentMillis = millis();

      if (currentMillis - previousMillis >= 500) {
        previousMillis = currentMillis;
        ledState = !ledState;
        digitalWrite(BLUE_LED, ledState ? LOW : HIGH);
      }

      if (millis() - lastSampleTime >= sampleInterval) {
        lastSampleTime += sampleInterval;

        float aX = myIMU.readFloatAccelX();
        float aY = myIMU.readFloatAccelY();
        float aZ = myIMU.readFloatAccelZ();
        float gX = myIMU.readFloatGyroX();
        float gY = myIMU.readFloatGyroY();
        float gZ = myIMU.readFloatGyroZ();

        int base = bufferIndex * 6;
        batchedData[base + 0] = aX;
        batchedData[base + 1] = aY;
        batchedData[base + 2] = aZ;
        batchedData[base + 3] = gX;
        batchedData[base + 4] = gY;
        batchedData[base + 5] = gZ;

        bufferIndex++;

        if (bufferIndex == samplesPerBatch) {
          bool sent = imuDataCharacteristic.writeValue((uint8_t*)batchedData, sizeof(float) * samplesPerBatch * 6);
          Serial.println(sent ? "✅ Batch sent" : "❌ BLE write failed");

          for (int i = 0; i < samplesPerBatch; i++) {
            int offset = i * 6;
            Serial.print(i); Serial.print(": ");
            for (int j = 0; j < 6; j++) {
              Serial.print(batchedData[offset + j], 3);
              Serial.print(j < 5 ? ", " : "\n");
            }
          }

          bufferIndex = 0;
          for (int i = 0; i < samplesPerBatch; i++) {
            for (int j = 0; j < 6; j++) {
              batchedData[i * 6 + j] = 0.0;
            }
          }
        }
      }
    }
  }

  digitalWrite(RED_LED, LOW);
  digitalWrite(BLUE_LED, HIGH);
}
