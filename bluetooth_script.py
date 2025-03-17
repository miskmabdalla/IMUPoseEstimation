import asyncio
from bleak import BleakScanner
from bleak import BleakClient


# device_address= ""
# device_service_UUID = ""
device_list = []


def detection_callback(device, advertisement_data):
    """Detects Arduino and saves its address and service UUID."""
    if device.name == "Arduino" and device.address not in device_list:
        # print(f"Name: {device.name}, Address: {device.address}, UUIDs: {advertisement_data.service_uuids}")
        # global device_address, device_service_UUID, 
        global device_list
        # device_address = device.address
        # device_service_UUID = advertisement_data.service_uuids[0]

        device_list.append(device.address)
        # device_tuple = (device_address, device_service_UUID)
        # device_list.append(device_tuple)




async def scanning():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)  
    await scanner.stop()

    # print(f"Device Address: {device_address}")
    # print(f"Service UUID:  {device_service_UUID}")
    # print(f"Characteristic UUID: {device_char_UUID}")


def notification_handler(uuid, sender, data):
    print(f"Received: {data.decode('utf-8')}")  # Convert bytes to string

async def read_characteristic(device_address):
    """Connects to the Arduino and subscribes to notifications."""

    if not device_address:
        print("Device address not found. Exiting.")
        return

    async with BleakClient(device_address) as client:
        if not client.is_connected:
            print("Failed to connect to device.")
            return

        print(f"Connected to {device_address}")
        print("Available Services & Characteristics:")
        device_char_UUID = None

        for service in client.services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f" - Characteristic: {char.uuid} (Properties: {char.properties})")
                
                # Select characteristic with 'notify' property
                if "notify" in char.properties:
                    device_char_UUID = char.uuid

        if not device_char_UUID:
            print("No suitable characteristic found. Exiting.")
            return
        
        print(f"Subscribing to characteristic {device_char_UUID}...")

        # Start receiving data
        await client.start_notify(device_char_UUID, notification_handler)

        # Keep connection alive to receive notifications
        await asyncio.sleep(30)  # Change this to how long you want to listen

        # Stop receiving data
        await client.stop_notify(device_char_UUID)


asyncio.run(scanning())
# Run the BLE client
for device in device_list:
    asyncio.run(read_characteristic(device))


# Name: Arduino, Address: 1B46F1B4-A2D2-6E21-BF55-2981B4B35216, UUIDs: ['19b10000-e8f2-537e-4f6c-d104768a1214']