#include <ArduinoBLE.h>
#include <LSM6DS3.h>
#include <Wire.h>

// Define onboard RGB LED pins
#define RED_LED LED_RED
#define GREEN_LED LED_GREEN
#define BLUE_LED LED_BLUE

// Create a BLE service
BLEService imuService("19B10000-E8F2-537E-4F6C-D104768A1214");

// Use binary BLE characteristic instead of string
BLECharacteristic imuDataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 150); // 3 samples x 6 floats x 4 bytes

// Create an instance of LSM6DS3 IMU sensor
LSM6DS3 myIMU(I2C_MODE, 0x6A);

// Batching config
const int samplesPerBatch = 6;       // 3 samples per BLE packet
float batchedData[samplesPerBatch][6];
int bufferIndex = 0;
const unsigned long sampleInterval = 20;  // 50 Hz
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
    // Serial.println("Starting Bluetooth Low Energy module failed!");
    while (1);
  }

  BLE.setLocalName("IMU_BLE_Device");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuDataCharacteristic);
  BLE.addService(imuService);
  BLE.advertise();

  // Serial.println("BLE IMU device is now advertising");
}

void loop() {
  static unsigned long previousMillis = 0;
  static bool ledState = false;

  BLEDevice central = BLE.central();

  if (central) {
    // Serial.print("Connected to central: ");
    // Serial.println(central.address());

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

        // Store in batch buffer
        batchedData[bufferIndex][0] = aX;
        batchedData[bufferIndex][1] = aY;
        batchedData[bufferIndex][2] = aZ;
        batchedData[bufferIndex][3] = gX;
        batchedData[bufferIndex][4] = gY;
        batchedData[bufferIndex][5] = gZ;
        bufferIndex++;

        if (bufferIndex == samplesPerBatch) {
          imuDataCharacteristic.writeValue((uint8_t*)batchedData, sizeof(batchedData));
          // if (imuDataCharacteristic.writeValue((uint8_t*)batchedData, sizeof(batchedData))) {
          //   Serial.println("Write OK");
          // } 
          // else {
          //   Serial.println("Write failed");
          // }
          // Serial.println("Batch sent:");
          // for (int i = 0; i < samplesPerBatch; i++) {
          //   Serial.print(i); Serial.print(": ");
          //   for (int j = 0; j < 6; j++) {
          //     Serial.print(batchedData[i][j], 3);
          //     Serial.print(j < 5 ? ", " : "\n");
          //   }
          // }
          bufferIndex = 0;
        }
      }
    }

    // Serial.print("Disconnected from central: ");
    // Serial.println(central.address());
  }

  digitalWrite(RED_LED, LOW);
  digitalWrite(BLUE_LED, HIGH);
}
