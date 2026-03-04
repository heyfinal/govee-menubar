import tkinter as tk
import json
import redis
import time

# Styling
BG_COLOR = "#1c1c1c"
TEXT_COLOR = "#d4d4d4"
ACCENT_COLOR = "#5a7d5a"
DIM_TEXT = "#6e6e6e"

class GoveeWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Govee Monitor")
        
        # Frameless and translucent
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg=BG_COLOR)
        
        # Position: Bottom Right (can be dragged)
        w, h = 220, 140
        self.root.geometry(f"{w}x{h}-50-50")
        
        # Main container
        self.frame = tk.Frame(self.root, bg=BG_COLOR, padx=15, pady=15)
        self.frame.pack(fill="both", expand=True)
        
        # Header
        self.title_label = tk.Label(self.frame, text="SENSOR MONITOR", font=("Inter", 10, "bold"), fg=DIM_TEXT, bg=BG_COLOR)
        self.title_label.pack(anchor="w")
        
        # Temp Row
        self.temp_frame = tk.Frame(self.frame, bg=BG_COLOR)
        self.temp_frame.pack(fill="x", pady=(5, 0))
        
        self.temp_val = tk.Label(self.temp_frame, text="--.-°", font=("SF Pro Display", 28, "bold"), fg=TEXT_COLOR, bg=BG_COLOR)
        self.temp_val.pack(side="left")
        
        self.temp_unit = tk.Label(self.temp_frame, text="F", font=("Inter", 14), fg=DIM_TEXT, bg=BG_COLOR, pady=10)
        self.temp_unit.pack(side="left")
        
        # Humidity & Battery Row
        self.stat_frame = tk.Frame(self.frame, bg=BG_COLOR)
        self.stat_frame.pack(fill="x")
        
        self.hum_label = tk.Label(self.stat_frame, text="HUMIDITY", font=("Inter", 8, "bold"), fg=DIM_TEXT, bg=BG_COLOR)
        self.hum_label.grid(row=0, column=0, sticky="w")
        
        self.hum_val = tk.Label(self.stat_frame, text="--%", font=("Inter", 12), fg=ACCENT_COLOR, bg=BG_COLOR)
        self.hum_val.grid(row=1, column=0, sticky="w")
        
        self.bat_label = tk.Label(self.stat_frame, text="BATTERY", font=("Inter", 8, "bold"), fg=DIM_TEXT, bg=BG_COLOR)
        self.bat_label.grid(row=0, column=1, sticky="w", padx=(20, 0))
        
        self.bat_val = tk.Label(self.stat_frame, text="--%", font=("Inter", 12), fg=TEXT_COLOR, bg=BG_COLOR)
        self.bat_val.grid(row=1, column=1, sticky="w", padx=(20, 0))

        # Dragging logic
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.update_data()
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def update_data(self):
        try:
            raw = self.r.get("govee_live_data")
            if raw:
                data = json.loads(raw)
                # Temperature (Convert to F)
                c = data.get("temperature", 0)
                f = (c * 9/5) + 32
                self.temp_val.config(text=f"{f:.1f}°")
                
                # Humidity
                h = data.get("humidity", "--")
                self.hum_val.config(text=f"{h}%")
                
                # Battery
                b = data.get("battery", "--")
                self.bat_val.config(text=f"{b}%")
                
                # Update title with device ID
                name = data.get("name", "Govee").split("_")[-1]
                self.title_label.config(text=f"SENSOR {name}")
        except Exception:
            pass
            
        self.root.after(2000, self.update_data) # Poll redis every 2s

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    widget = GoveeWidget()
    widget.run()
