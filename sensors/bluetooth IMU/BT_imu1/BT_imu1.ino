#include <ArduinoBLE.h>
#include <LSM6DS3.h>
#include <Wire.h>

// Define onboard RGB LED pins
#define RED_LED LED_RED
#define GREEN_LED LED_GREEN
#define BLUE_LED LED_BLUE

// Create a BLE service
BLEService imuService("19B10000-E8F2-537E-4F6C-D104768A1214");

// Create a BLE characteristic for IMU data
BLEStringCharacteristic imuDataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 200);

// Create an instance of LSM6DS3 IMU sensor
LSM6DS3 myIMU(I2C_MODE, 0x6A);

// Batching config
const int batchSize = 3;
String imuBuffer[batchSize];
int bufferIndex = 0;
const unsigned long sampleInterval = 100;  // 50 Hz
unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);  // Wait for Serial (3s max) - helps with debugging

  // Set LED pins as outputs
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);

  // --- SOLID RED ON STARTUP ---
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(BLUE_LED, HIGH);
  digitalWrite(RED_LED, LOW);  // RED ON (Solid)

  delay(500);  // Ensure visibility

  // Initialize IMU
  if (myIMU.begin() != 0) {
    Serial.println("IMU Device error");
  } else {
    Serial.println("aX,aY,aZ,gX,gY,gZ");
  }

  delay(300);  // Small delay before BLE starts

  // Initialize BLE
  if (!BLE.begin()) {
    Serial.println("Starting Bluetooth Low Energy module failed!");
    while (1);
  }

  BLE.setLocalName("IMU_BLE_Device");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuDataCharacteristic);
  BLE.addService(imuService);
  BLE.advertise();

  Serial.println("BLE IMU device is now advertising");
}

void loop() {
  static unsigned long previousMillis = 0;
  static bool ledState = false;

  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    // Turn OFF RED LED and start BLUE blinking
    digitalWrite(RED_LED, HIGH);

    while (central.connected()) {
      unsigned long currentMillis = millis();

      // Blink BLUE LED every 500ms
      if (currentMillis - previousMillis >= 500) {
        previousMillis = currentMillis;
        ledState = !ledState;
        digitalWrite(BLUE_LED, ledState ? LOW : HIGH);
      }

      // Sampling logic
      if (millis() - lastSampleTime >= sampleInterval) {
        lastSampleTime += sampleInterval;

        float aX = myIMU.readFloatAccelX();
        float aY = myIMU.readFloatAccelY();
        float aZ = myIMU.readFloatAccelZ();
        float gX = myIMU.readFloatGyroX();
        float gY = myIMU.readFloatGyroY();
        float gZ = myIMU.readFloatGyroZ();

        // Store sample in batch buffer
        imuBuffer[bufferIndex] = String(aX, 3) + "," + String(aY, 3) + "," + String(aZ, 3) + "," +
                                 String(gX, 3) + "," + String(gY, 3) + "," + String(gZ, 3);
        bufferIndex++;

        // If buffer full, send BLE notification with all samples
        if (bufferIndex == batchSize) {
          String payload = imuBuffer[0];
          for (int i = 1; i < batchSize; i++) {
            payload += "\n" + imuBuffer[i];
          }

          imuDataCharacteristic.writeValue(payload);

          Serial.println(payload);
          Serial.print("Payload length: ");
          Serial.println(payload.length());

          bufferIndex = 0;  // Reset buffer
        }
      }
    }

    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }

  // --- SOLID RED WHEN NOT CONNECTED ---
  digitalWrite(RED_LED, LOW);  // Ensure RED LED is solid
  digitalWrite(BLUE_LED, HIGH);  // Ensure BLUE is OFF
}