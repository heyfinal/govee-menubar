#!/usr/bin/env python3.12
"""Read temperature and humidity from Govee BLE sensor (FEB9 service)."""
import asyncio
import struct
import sys
from datetime import datetime

from bleak import BleakClient, BleakScanner

GOVEE_SERVICE = "0000feb9-0000-1000-8000-00805f9b34fb"
READ_CHAR = "00002ab9-0000-1000-8000-00805f9b34fb"
GOVEE_MFR_ID = 0x00C4

# CoreBluetooth UUID — set after first discovery, not the LG TV
KNOWN_ADDR = ""


def decode_reading(data: bytes) -> dict:
    """Decode 6-byte GATT reading: [status, temp_hi, temp_lo, hum_hi, hum_lo, flags]"""
    if len(data) < 5:
        raise ValueError(f"Short data: {data.hex()}")
    temp_mc = struct.unpack(">h", data[1:3])[0]   # millidegrees C, signed BE
    hum_mp = struct.unpack(">H", data[3:5])[0]    # milli-percent, unsigned BE
    temp_c = temp_mc / 1000
    temp_f = temp_c * 9 / 5 + 32
    humidity = hum_mp / 1000
    battery = (data[5] & 0x7F) if len(data) > 5 else None
    return {
        "temp_c": temp_c,
        "temp_f": temp_f,
        "humidity": humidity,
        "battery": battery,
        "raw": data.hex(),
    }


async def scan_and_read(timeout: float = 60.0) -> dict:
    """Scan for the Govee sensor, then connect and read once found."""
    result_future: asyncio.Future = asyncio.get_event_loop().create_future()

    async def on_detected(device, adv):
        if result_future.done():
            return
        is_govee = (
            GOVEE_SERVICE in adv.service_uuids
            or GOVEE_MFR_ID in adv.manufacturer_data
            or device.address == KNOWN_ADDR
        )
        if not is_govee:
            return
        print(f"Sensor found: {device.address}", file=sys.stderr)
        result_future.set_result(device)

    async with BleakScanner(detection_callback=on_detected):
        try:
            device = await asyncio.wait_for(result_future, timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeError("Govee sensor not found within scan window")

        # Connect while scanner is still active (keeps device in CB cache)
        print("Connecting...", file=sys.stderr)
        async with BleakClient(device, timeout=15) as client:
            raw = await client.read_gatt_char(READ_CHAR)
            return decode_reading(bytes(raw))


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Read Govee temp/humidity sensor")
    parser.add_argument("--watch", type=int, metavar="SECS", default=0,
                        help="Poll every N seconds continuously (0 = single read)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    while True:
        reading = await scan_and_read()
        ts = datetime.now().strftime("%H:%M:%S")

        if args.json:
            import json
            print(json.dumps({"time": ts, **reading}), flush=True)
        else:
            bat = f"  bat:{reading['battery']}%" if reading["battery"] is not None else ""
            print(f"[{ts}]  {reading['temp_c']:.2f}°C ({reading['temp_f']:.1f}°F)  |  {reading['humidity']:.1f}% RH{bat}")

        if not args.watch:
            break
        await asyncio.sleep(args.watch)


asyncio.run(main())
