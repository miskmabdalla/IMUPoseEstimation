import threading
import asyncio
from bleak import BleakClient, BleakScanner
import csv
import os
import struct
import time
from pathlib import Path

DATA_DIR = "dataset/imu_data"
os.makedirs(DATA_DIR, exist_ok=True)

pressed_flag = True  # Set to True for now; hook to key listener if needed
exit_flag = False    # Thread-safe exit indicator


def decode_batched_floats(data, samples_per_batch=6, floats_per_sample=6):
    expected_len = samples_per_batch * floats_per_sample * 4
    if len(data) != expected_len:
        print(f"Unexpected packet size: {len(data)} bytes (expected {expected_len})")
        return []

    floats = struct.unpack("<" + "f" * samples_per_batch * floats_per_sample, data)
    return [floats[i:i+floats_per_sample] for i in range(0, len(floats), floats_per_sample)]


async def connect_and_log(sensor_address, char_uuid, csv_path):
    try:
        async with BleakClient(sensor_address) as client:
            if not client.is_connected:
                print(f"Failed to connect: {sensor_address}")
                return

            print(f"Connected: {sensor_address}")

            def notification_handler(sender, data):
                if not pressed_flag:
                    return

                samples = decode_batched_floats(data)
                now = time.time()
                dt = 0.02
                with open(csv_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    for i, sample in enumerate(samples):
                        t = now - dt * (len(samples) - 1 - i)
                        writer.writerow([t] + list(sample))

            await client.start_notify(char_uuid, notification_handler)
            print(f"Started notifications: {sensor_address}")

            while not exit_flag:
                await asyncio.sleep(0.1)

            await client.stop_notify(char_uuid)
            print(f"Stopped notifications: {sensor_address}")

    except Exception as e:
        print(f"Exception with {sensor_address}: {e}")


def ble_thread_worker(sensor_address, char_uuid, csv_path):
    asyncio.run(connect_and_log(sensor_address, char_uuid, csv_path))


def main():
    trial_base = Path(DATA_DIR)
    existing_trials = [int(p.name.split("_")[1]) for p in trial_base.glob("trial_*") if p.name.startswith("trial_") and p.name.split("_")[1].isdigit()]
    trial_num = max(existing_trials) + 1 if existing_trials else 1
    trial_path = trial_base / f"trial_{trial_num}"
    trial_path.mkdir()

    print(f"Created trial folder: {trial_path}")

    found_devices = {}

    async def scan():
        def detection_callback(device, adv):
            if (device.name == "IMU_BLE_Device") and adv.service_uuids:
                found_devices[device.address] = adv.service_uuids[0]
                print(f"Found {device.address} with UUID {adv.service_uuids[0]}")

        scanner = BleakScanner(detection_callback)
        await scanner.start()
        await asyncio.sleep(5)
        await scanner.stop()

    asyncio.run(scan())

    threads = []
    for addr, uuid in found_devices.items():
        filename = f"{addr.replace(':', '_')}.csv"
        filepath = trial_path / filename
        with open(filepath, "w") as f:
            f.write("Timestamp,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ\n")

        t = threading.Thread(target=ble_thread_worker, args=(addr, uuid, str(filepath)))
        t.start()
        threads.append(t)
        time.sleep(2)  # Avoid connection collision

    try:
        print("Press Ctrl+C to stop logging...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        global exit_flag
        exit_flag = True
        for t in threads:
            t.join()
        print("All threads stopped.")


if __name__ == "__main__":
    main()
