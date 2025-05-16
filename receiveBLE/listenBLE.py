import asyncio
from bleak import BleakClient
import time

ADDRESS = "78:21:84:E4:C0:7A"  
CHARACTERISTIC_UUID = "abcd1234-5678-90ab-cdef-1234567890ab"
image_data = bytearray()

def handle_data(sender, data):
    global image_data
    image_data.extend(data)
    print(f"Received {len(data)} bytes... Total: {len(image_data)}")

async def main():
    async with BleakClient(ADDRESS) as client:
        await client.start_notify(CHARACTERISTIC_UUID, handle_data)
        print("Receiving image data...")
        await asyncio.sleep(10)  # Thời gian chờ nhận dữ liệu
        #image name is current time
        image_name = f"image/image_{int(time.time())}.jpg"
        with open(image_name, "wb") as f:
            f.write(image_data)
        print("Image saved.")

asyncio.run(main())
