from bleak import BleakScanner
import asyncio

async def scan_ble():
    devices = await BleakScanner.discover(timeout=5.0)
    if devices:
        print("Đã tìm thấy thiết bị BLE:")
        for d in devices:
            print(f"{d.name} - {d.address}")
    else:
        print("Không tìm thấy thiết bị BLE nào.")

asyncio.run(scan_ble())
