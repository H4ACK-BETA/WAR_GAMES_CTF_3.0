"""File server to distribute the generated PCAP."""
import os
from flask import Flask, send_file, render_template_string

app = Flask(__name__)
PCAP_PATH = "/app/exposure_window.pcap"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>4r34::51 — CLASSIFIED</title>
<style>
body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #c0392b;
       padding: 40px; display: flex; align-items: center; justify-content: center; min-height: 90vh; }
.card { background: #111; border: 2px solid #c0392b; border-radius: 0; padding: 40px;
        max-width: 550px; text-align: center; }
h1 { color: #e74c3c; margin-bottom: 5px; font-size: 1.8em; }
.subtitle { color: #666; margin-bottom: 25px; }
a { color: #e74c3c; font-size: 1.3em; text-decoration: none; border: 1px solid #e74c3c;
    padding: 10px 25px; display: inline-block; }
a:hover { background: #e74c3c; color: #000; }
.meta { color: #333; font-size: 0.8em; margin-top: 25px; }
.warning { color: #c0392b; font-size: 0.7em; margin-top: 15px; letter-spacing: 2px; }
</style></head>
<body>
<div class="card">
    <h1>⚠ CLASSIFIED ⚠</h1>
    <p class="subtitle">INCIDENT #4R34-51 | EXPOSURE WINDOW CAPTURE</p>
    <br>
    <a href="/download">↓ DOWNLOAD PCAP</a>
    <p class="meta">{{ size }} bytes | 45-second capture window</p>
    <p class="warning">TOP SECRET // UMBRA // COSMIC</p>
</div>
</body></html>
"""

@app.route("/")
def index():
    size = os.path.getsize(PCAP_PATH) if os.path.exists(PCAP_PATH) else 0
    return render_template_string(TEMPLATE, size=f"{size:,}")

@app.route("/download")
def download():
    return send_file(PCAP_PATH, as_attachment=True, download_name="exposure_window.pcap")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
