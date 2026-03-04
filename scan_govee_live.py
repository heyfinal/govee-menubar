import asyncio
import sys
from bleak import BleakScanner

async def main():
    print("Starting scan for 15 seconds...")
    def callback(device, adv):
        name = adv.local_name or device.name or ""
        is_govee = "Govee" in name or name.startswith("GV") or any(m in adv.manufacturer_data for m in [0xEC88, 0x0001])
        if is_govee:
            print(f"\nFOUND: {name} ({device.address}) RSSI: {adv.rssi}")
            print(f"  Mfr Data: {adv.manufacturer_data}")

    try:
        scanner = BleakScanner(detection_callback=callback)
        await scanner.start()
        for i in range(15):
            await asyncio.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
        await scanner.stop()
        print("\nScan finished.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
