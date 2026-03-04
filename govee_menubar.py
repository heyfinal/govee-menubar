import rumps
import redis
import json
import asyncio

class GoveeStatusBarApp(rumps.App):
    def __init__(self):
        super(GoveeStatusBarApp, self).__init__("Govee")
        self.title = "--.-°F"
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Menu items
        self.hum_item = rumps.MenuItem("Humidity: --%")
        self.bat_item = rumps.MenuItem("Battery: --%")
        self.rssi_item = rumps.MenuItem("Signal: -- dBm")
        self.menu = [self.hum_item, self.bat_item, self.rssi_item]

    @rumps.timer(5)
    def update_data(self, _):
        try:
            raw = self.r.get("govee_live_data")
            if raw:
                data = json.loads(raw)
                # Temperature (Convert to F)
                c = data.get("temperature", 0)
                f = (c * 9/5) + 32
                self.title = f"{f:.1f}°F"
                
                # Update Menu
                self.hum_item.title = f"Humidity: {data.get('humidity', '--')}%"
                self.bat_item.title = f"Battery: {data.get('battery', '--')}%"
                self.rssi_item.title = f"Signal: {data.get('rssi', '--')} dBm"
        except Exception:
            pass

if __name__ == "__main__":
    app = GoveeStatusBarApp()
    app.run()
