#!/usr/bin/env python3.12
"""Serve a 24h temperature & humidity chart from Redis history."""
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

import redis

PORT = 8099
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

HTML = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Govee 24h Sensor History</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3"></script>
<style>
  body { margin: 0; background: #1a1a2e; display: flex; justify-content: center; align-items: center; height: 100vh; }
  canvas { max-width: 1100px; max-height: 600px; }
</style>
</head><body>
<canvas id="chart"></canvas>
<script>
async function load() {
  const res = await fetch('/api/history');
  const data = await res.json();
  const labels = data.map(d => new Date(d.ts * 1000));
  const temps = data.map(d => (d.temperature * 9/5) + 32);
  const hums = data.map(d => d.humidity);

  const ctx = document.getElementById('chart');
  if (window._chart) window._chart.destroy();
  window._chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Temperature (°F)', data: temps, borderColor: '#e94560', backgroundColor: 'rgba(233,69,96,0.1)', yAxisID: 'y', tension: 0.3, pointRadius: 0 },
        { label: 'Humidity (%)', data: hums, borderColor: '#0f3460', backgroundColor: 'rgba(15,52,96,0.1)', yAxisID: 'y1', tension: 0.3, pointRadius: 0 }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { labels: { color: '#eee', font: { size: 14 } } } },
      scales: {
        x: { type: 'time', time: { unit: 'hour', displayFormats: { hour: 'ha' } }, ticks: { color: '#aaa' }, grid: { color: '#333' } },
        y: { position: 'left', title: { display: true, text: '°F', color: '#e94560' }, ticks: { color: '#e94560' }, grid: { color: '#333' } },
        y1: { position: 'right', title: { display: true, text: '%', color: '#0f3460' }, ticks: { color: '#0f3460' }, grid: { drawOnChartArea: false } }
      }
    }
  });
}
load();
setInterval(load, 60000);
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/history":
            raw = r.zrangebyscore("govee_history", "-inf", "+inf")
            data = [json.loads(entry) for entry in raw]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())

    def log_message(self, fmt, *args):
        pass  # silence request logs


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Govee graph at http://127.0.0.1:{PORT}")
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    server.serve_forever()
