import asyncio
import json
import os
import redis
from bleak import BleakScanner
from govee_ble import GoveeBluetoothDeviceData
from home_assistant_bluetooth import BluetoothServiceInfo

# Connect to local redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def callback(device, adv):
    name = str(adv.local_name or device.name or "")
    if not (name.startswith("Govee_") or name.startswith("GV")):
        return
        
    sensor = GoveeBluetoothDeviceData()
    mfr_data = {int(k): bytes(v) for k, v in adv.manufacturer_data.items()}
    
    service_info = BluetoothServiceInfo(
        name=name, address=str(device.address), rssi=adv.rssi,
        manufacturer_data=mfr_data,
        service_data={str(k): bytes(v) for k, v in adv.service_data.items()},
        service_uuids=[str(u) for u in adv.service_uuids],
        source="local",
    )
    
    data = sensor.update(service_info)
    if data.entity_values:
        sensor_data = {}
        for device_key, entity in data.entity_values.items():
            key = str(getattr(device_key, "key", device_key))
            sensor_data[key] = entity.native_value
        
        sensor_data["name"] = name
        sensor_data["rssi"] = adv.rssi
        sensor_data["last_update"] = asyncio.get_event_loop().time()
        
        # Store in redis for the widget to read
        r.set("govee_live_data", json.dumps(sensor_data))
        
        # Also write to a local file for the Swift widget
        file_path = os.path.expanduser("~/govee_data.json")
        with open(file_path, "w") as f:
            json.dump(sensor_data, f)
            
        print(f"Updated: {name} - {sensor_data.get('temperature')}°C")

async def main():
    print("Govee Daemon started. Listening for broadcasts...")
    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    while True:
        await asyncio.sleep(3600) # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
