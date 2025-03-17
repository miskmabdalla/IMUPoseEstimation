import asyncio
from bleak import BleakScanner
from bleak import BleakClient
import os
import csv
import time

device_list = {}
DATA_DIR = "imu_data"
os.makedirs(DATA_DIR, exist_ok=True)

def detection_callback(device, advertisement_data):
    """Detects Arduino and saves its address and service UUID."""
    # print(f"Name : {device.name},  Address: {device.address}")
    if (device.name == "Arduino" or device.name == "IMU_BLE_Device") and device.address not in device_list:
        if advertisement_data.service_uuids:
            device_list[device.address] = advertisement_data.service_uuids[0]
            print(f"Found Arduino - Address: {device.address}, Service UUID: {advertisement_data.service_uuids[0]}")





async def scanning():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)  
    await scanner.stop()

class IMUSensor:
    def __init__(self, device_address: str, device_service_UUID: str):
        self.device_address = device_address
        self.device_service_UUID = device_service_UUID
        self.device_char_UUID = None  # To be set dynamically
        self.file_path = os.path.join(DATA_DIR, f"{self.device_address.replace(':', '')}.csv")

        with open(self.file_path, "w") as f:
            f.write("Timestamp,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ\n")

    def __str__(self):
        return f"IMU Sensor at {self.device_address} (Service UUID: {self.device_service_UUID})"


    
    async def read_characteristic(self):
        """Connects to the sensor and subscribes to notifications."""
        async with BleakClient(self.device_address) as client:
            if not client.is_connected:
                print(f"Failed to connect to {self.device_address}")
                return

            print(f"Connected to {self.device_address}")
            print("Discovering services and characteristics...")

            # Get available services
            await client.get_services()
            for service in client.services:
                for char in service.characteristics:
                    if "notify" in char.properties:
                        self.device_char_UUID = char.uuid
                        break  # Use first available notify characteristic

            if not self.device_char_UUID:
                print(f"No suitable characteristic found for {self.device_address}.")
                return

            print(f"Subscribing to characteristic {self.device_char_UUID}...")

            

            async def notification_handler(sender, data):
                """Handles incoming sensor data."""
                decoded_data = data.decode("utf-8")
                print(f"[{self.device_address}] Received: {decoded_data}")

                with open(self.file_path, "a", newline="") as f:
                    # writer = csv.writer(f)
                    # writer.writerow([decoded_data])
                    writer = csv.writer(f)
                    writer.writerow([time.time()] + decoded_data.split(","))

            # Start receiving data
            await client.start_notify(self.device_char_UUID, notification_handler)

            await asyncio.sleep(30)  # Adjust listening duration as needed

            await client.stop_notify(self.device_char_UUID)
            print(f"Stopped notifications for {self.device_address}")




async def main():
    await scanning()  # Scan for devices first

    if not device_list:
        print("No Arduino devices found.")
        return

    sensors = [IMUSensor(addr, service_uuid) for addr, service_uuid in device_list.items()]

    # Read data from all sensors concurrently
    await asyncio.gather(*(sensor.read_characteristic() for sensor in sensors))

# Run the script
asyncio.run(main())


