#!/usr/bin/env python3.12
"""Discover Govee BLE sensors — run this to find your sensor's UUID."""
import asyncio
from bleak import BleakScanner

# Known non-Govee devices to skip
SKIP_NAMES = set()  # add device names to skip here
APPLE_MFR = 0x004C

seen = {}

def callback(device, adv):
    addr = device.address
    name = adv.local_name or device.name or ""

    # Skip known Apple/LG devices
    if name in SKIP_NAMES:
        return
    if adv.manufacturer_data and all(k == APPLE_MFR for k in adv.manufacturer_data):
        return

    if addr in seen:
        return
    seen[addr] = True

    display_name = name or "(unnamed)"
    print(f"Device: {display_name}")
    print(f"  UUID:    {addr}")
    print(f"  RSSI:    {adv.rssi} dBm")
    for mid, data in adv.manufacturer_data.items():
        print(f"  Mfr 0x{mid:04X}: {data.hex()}")
    for u in adv.service_uuids:
        print(f"  Service: {u}")
    print()

async def main():
    print("Scanning for non-Apple BLE devices for 60 seconds...\n")
    async with BleakScanner(detection_callback=callback):
        await asyncio.sleep(60)
    print(f"Done. Found {len(seen)} unique non-Apple devices.")

asyncio.run(main())
