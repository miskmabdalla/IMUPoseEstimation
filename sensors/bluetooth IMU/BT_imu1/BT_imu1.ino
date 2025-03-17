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
BLEStringCharacteristic imuDataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 64);

// Create an instance of LSM6DS3 IMU sensor
LSM6DS3 myIMU(I2C_MODE, 0x6A);

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // Set LED pins as outputs
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);

  // Ensure all LEDs are OFF initially
  digitalWrite(RED_LED, HIGH);
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(BLUE_LED, HIGH);

  if (myIMU.begin() != 0) {
    Serial.println("IMU Device error");
  } else {
    Serial.println("aX,aY,aZ,gX,gY,gZ");
  }

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
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    unsigned long previousMillis = 0;
    bool ledState = false;

    while (central.connected()) {
      unsigned long currentMillis = millis();

      // Blink RED LED every 500ms (ON when LOW, OFF when HIGH)
      if (currentMillis - previousMillis >= 500) {
        previousMillis = currentMillis;
        ledState = !ledState;
        digitalWrite(RED_LED, ledState ? LOW : HIGH);  // Toggle LED
      }

      float aX = myIMU.readFloatAccelX();
      float aY = myIMU.readFloatAccelY();
      float aZ = myIMU.readFloatAccelZ();
      float gX = myIMU.readFloatGyroX();
      float gY = myIMU.readFloatGyroY();
      float gZ = myIMU.readFloatGyroZ();
      
      // Format data as CSV
      String imuData = String(aX, 3) + "," + String(aY, 3) + "," + String(aZ, 3) + "," +
                       String(gX, 3) + "," + String(gY, 3) + "," + String(gZ, 3);
      
      imuDataCharacteristic.writeValue(imuData);
      Serial.println(imuData);
      
      delay(100); // Adjust delay based on required data rate
    }

    // Turn OFF all LEDs when disconnected
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(BLUE_LED, HIGH);
    
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}
