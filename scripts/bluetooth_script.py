import asyncio
from bleak import BleakScanner
from bleak import BleakClient
import os
import csv
import time
import matplotlib.pyplot as plt
import pandas as pd
from pynput.keyboard import Listener
from pathlib import Path


device_list = {}
timestamp = ""
DATA_DIR = "dataset/imu_data"
pressed_flag = False
os.makedirs(DATA_DIR, exist_ok=True)
exit_event = asyncio.Event()

def detection_callback(device, advertisement_data):
    """Detects Arduino and saves its address and service UUID."""
    # print(f"Name : {device.name},  Address: {device.address}")
    if (device.name == "Arduino" or device.name == "IMU_BLE_Device") and device.address not in device_list:
    # if (device.name == "Arduino" or device.name == "IMU_BLE_Device") and (device.address not in device_list) and (device.address != '1B46F1B4-A2D2-6E21-BF55-2981B4B35216'):
    # if (device.name == "Arduino" or device.name == "IMU_BLE_Device") and (device.address not in device_list) and (device.address != 'C22972B9-EA89-C4CD-E9F5-6369FB2653E6'):
        if advertisement_data.service_uuids:
            device_list[device.address] = advertisement_data.service_uuids[0]
            print(f"Found Arduino - Address: {device.address}, Service UUID: {advertisement_data.service_uuids[0]}")





async def scanning():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)  
    await scanner.stop()



class IMUSensor:
    def __init__(self, device_address: str, device_service_UUID: str, trial_folder: str):
        self.device_address = device_address
        self.device_service_UUID = device_service_UUID
        self.device_char_UUID = None

        # Create CSV file in the shared trial folder, named with sensor address
        filename = f"{self.device_address.replace(':', '_')}.csv"
        self.file_path = os.path.join(trial_folder, filename)

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
            for service in client.services:
                for char in service.characteristics:
                    if "notify" in char.properties:
                        self.device_char_UUID = char.uuid
                        break

            if not self.device_char_UUID:
                print(f"No suitable characteristic found for {self.device_address}.")
                return

            print(f"Subscribing to characteristic {self.device_char_UUID}...")

            async def notification_handler(sender, data):
                """Handles incoming sensor data with extrapolated timestamps."""
                if not pressed_flag:
                    return

                decoded = data.decode("utf-8").strip()
                lines = decoded.split("\n")

                # Compute timestamps by back-calculating from current time
                self.last_timestamp = getattr(self, "last_timestamp", 0)
                now = time.time()
                dt = 0.02  # 50Hz assumed
                with open(self.file_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    for i, line in enumerate(lines):
                        parts = line.strip().split(",")
                        if len(parts) == 6:
                            t = now - dt * (len(lines) - 1 - i)
                            t = max(t, self.last_timestamp + dt)  # enforce strict monotonicity
                            self.last_timestamp = t
                            writer.writerow([t] + parts)

            await client.start_notify(self.device_char_UUID, notification_handler)
            while not exit_event.is_set():
                await asyncio.sleep(0.1)  # Adjust listening duration as needed
            await client.stop_notify(self.device_char_UUID)
            print(f"Stopped notifications for {self.device_address}")



async def main():
    # Create imu_data/ if it doesn't exist
    trial_base = Path("dataset/imu_data")
    trial_base.mkdir(exist_ok=True)

    # Scan existing trial folders
    existing_trials = [
        int(p.name.split("_")[1])
        for p in trial_base.glob("trial_*")
        if p.name.startswith("trial_") and p.name.split("_")[1].isdigit()
    ]

    # Handle empty directory
    trial_num = max(existing_trials) + 1 if existing_trials else 1
    trial_path = trial_base / f"trial_{trial_num}"
    trial_path.mkdir()

    print(f" Created trial folder: {trial_path}")

    # Start BLE scanning
    await scanning()

    if not device_list:
        print("No Arduino devices found.")
        return

    # Create sensor handlers
    sensors = [
        IMUSensor(addr, uuid, str(trial_path))
        for addr, uuid in device_list.items()
    ]

    def on_press(key):
        global pressed_flag
        try:
            if key.char == 'r':
                pressed_flag = True
                print("Recording started")
        except AttributeError:
            if key == key.esc:
                print("ESC pressed — stopping...")
                exit_event.set()
            

    listener = Listener(on_press=on_press)
    listener.start()
    # Run all sensor readers concurrently
    sensor_tasks = []
    for i, sensor in enumerate(sensors):
        await asyncio.sleep(0.25 * i)
        sensor_tasks.append(sensor.read_characteristic())

    await asyncio.gather(*sensor_tasks)

    # Keep loop alive
    while True:
        await asyncio.sleep(3600)


# Run the script
asyncio.run(main())


