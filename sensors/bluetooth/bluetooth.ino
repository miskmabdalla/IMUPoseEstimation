#include <ArduinoBLE.h>

BLEService ledService("19B10000-E8F2-537E-4F6C-D104768A1214"); // Bluetooth Low Energy Service

const int ledPin = LED_BUILTIN; // Pin to use for the LED

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // Set LED pin to output mode
  pinMode(ledPin, OUTPUT);

  // Begin initialization
  if (!BLE.begin()) {
    Serial.println("Starting Bluetooth Low Energy module failed!");
    while (1);
  }

  // Set advertised local name and service UUID
  BLE.setLocalName("BLE_Device");
  BLE.setAdvertisedService(ledService);
  
  // Add service
  BLE.addService(ledService);

  // Start advertising
  BLE.advertise();

  Serial.println("BLE device is now advertising");
}

void loop() {
  // Listen for BLE central devices to connect
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    // Keep connection active while central is connected
    while (central.connected()) {
      delay(100); // Prevent excessive loop execution
    }

    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}
