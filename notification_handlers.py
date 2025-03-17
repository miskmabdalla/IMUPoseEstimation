DEVICE_UUID_ASSIGNMENT = {
    "imu_1": "19b10000-e8f2-537e-4f6c-d104768a1214",
    "imu_2": "29b10000-e8f2-537e-4f6c-d104768a1214",
    "imu_3": "39b10000-e8f2-537e-4f6c-d104768a1214",
    "imu_4": "49b10000-e8f2-537e-4f6c-d104768a1214",
    "imu_5": "59b10000-e8f2-537e-4f6c-d104768a1214",
    "imu_6": "69b10000-e8f2-537e-4f6c-d104768a1214"
}

# Function to handle incoming BLE notifications
def main_notification_handler(uuid, sender, data):
    print(f"Received: {data.decode('utf-8')}")  # Convert bytes to string
    with open(f"{uuid}.csv", "a") as f:
        f.write({data.decode('utf-8')} + "\n")

def imu_1_notification_handler(sender, data):
    main_notification_handler(DEVICE_UUID_ASSIGNMENT["imu_1"], sender, data)