"""File server for distributing the PCAP."""
import os
from flask import Flask, send_file, render_template_string

app = Flask(__name__)
PCAP_PATH = "/app/beacon_capture.pcap"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>sh4d0w::b34c0n</title>
<style>
body { font-family: monospace; background: #0d1117; color: #58a6ff;
       padding: 40px; display: flex; align-items: center; justify-content: center; min-height: 90vh; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 40px;
        max-width: 500px; text-align: center; }
h1 { color: #f0883e; margin-bottom: 10px; }
a { color: #58a6ff; font-size: 1.2em; text-decoration: none; border: 1px solid #58a6ff;
    padding: 10px 25px; display: inline-block; margin-top: 15px; }
a:hover { background: #58a6ff; color: #0d1117; }
.meta { color: #484f58; font-size: 0.8em; margin-top: 20px; }
</style></head>
<body>
<div class="card">
    <h1>🛰 BEACON DETECTED</h1>
    <p>SOC Alert — Periodic outbound from WS-FIN-042</p>
    <p>8-minute capture window preserved.</p>
    <a href="/download">⬇ Download PCAP</a>
    <p class="meta">{{ size }} bytes | ~8 min capture</p>
</div>
</body></html>
"""

@app.route("/")
def index():
    size = os.path.getsize(PCAP_PATH) if os.path.exists(PCAP_PATH) else 0
    return render_template_string(TEMPLATE, size=f"{size:,}")

@app.route("/download")
def download():
    return send_file(PCAP_PATH, as_attachment=True, download_name="beacon_capture.pcap")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
