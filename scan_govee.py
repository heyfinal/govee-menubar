import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for Govee sensors...")
    devices = await BleakScanner.discover(timeout=10.0)
    found = False
    for d in devices:
        name = d.name or ""
        if "Govee" in name or name.startswith("GV"):
            print(f"Found: {name} ({d.address})")
            found = True
    if not found:
        print("No Govee sensors found in 10s scan.")

if __name__ == "__main__":
    asyncio.run(main())
