import asyncio
import sys
from bleak import BleakScanner
from govee_ble import GoveeBluetoothDeviceData
from home_assistant_bluetooth import BluetoothServiceInfo

# Map sensor keys to readable labels
KEY_MAP = {
    "temperature": "Temperature",
    "humidity": "Humidity",
    "battery": "Battery"
}

def callback(device, adv):
    # macOS returns objc types that the HA parser doesn't like
    # Force convert to standard Python strings/bytes
    name = str(adv.local_name or device.name or "")
    address = str(device.address)
    
    # Govee sensors usually start with Govee_ or GV
    if not (name.startswith("Govee_") or name.startswith("GV")):
        return
        
    sensor = GoveeBluetoothDeviceData()
    
    # Clean manufacturer data: ensure keys are ints and values are bytes
    mfr_data = {int(k): bytes(v) for k, v in adv.manufacturer_data.items()}
    
    service_info = BluetoothServiceInfo(
        name=name,
        address=address,
        rssi=adv.rssi,
        manufacturer_data=mfr_data,
        service_data={str(k): bytes(v) for k, v in adv.service_data.items()},
        service_uuids=[str(u) for u in adv.service_uuids],
        source="local",
    )
    
    # Update and parse the advertisement data
    data = sensor.update(service_info)
    
    # Check if we have valid readings
    if data.entity_values:
        print(f"\n--- {name} ---")
        for device_key, entity in data.entity_values.items():
            # handle DeviceKey objects from sensor-state-data
            key = str(getattr(device_key, "key", device_key))
            
            label = KEY_MAP.get(key, key.capitalize())
            unit = "°C" if key == "temperature" else "%" if key == "humidity" else "%" if key == "battery" else ""
            
            # Convert C to F for temperature
            if key == "temperature":
                val_f = (entity.native_value * 9/5) + 32
                print(f"{label}: {entity.native_value:.1f}{unit} ({val_f:.1f}°F)")
            else:
                print(f"{label}: {entity.native_value}{unit}")
        print(f"Signal Strength: {adv.rssi} dBm")

async def main():
    print("Linking to Govee sensor near machine...")
    print("Searching for BLE advertisements (this may take up to 30s)...")
    
    try:
        scanner = BleakScanner(detection_callback=callback)
        await scanner.start()
        # Stay active to catch the next broadcast (usually every 10-30s)
        await asyncio.sleep(60)
        await scanner.stop()
    except Exception as e:
        print(f"\nError: {e}")
        if "permission" in str(e).lower():
            print("\nTIP: Please ensure Terminal/iTerm2 has Bluetooth permissions in System Settings.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
