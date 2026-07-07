"""Simple file server to distribute the generated PCAP."""
import os
from flask import Flask, send_file, render_template_string

app = Flask(__name__)
PCAP_PATH = "/app/capture.pcap"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>gh0st::exf1l</title>
<style>
body { font-family: monospace; background: #0a0e17; color: #8892b0; padding: 40px;
       display: flex; align-items: center; justify-content: center; min-height: 90vh; }
.card { background: #112240; border: 1px solid #1d3461; border-radius: 10px; padding: 40px;
        max-width: 500px; text-align: center; }
h1 { color: #64ffda; margin-bottom: 15px; }
a { color: #64ffda; font-size: 1.2em; }
.meta { color: #495670; font-size: 0.85em; margin-top: 20px; }
</style></head>
<body>
<div class="card">
    <h1>📡 Incident #4471</h1>
    <p>BACKUP-SRV-03 packet capture is ready for analysis.</p>
    <br>
    <a href="/download">⬇ Download capture.pcap</a>
    <p class="meta">{{ size }} bytes | Generated for your team</p>
</div>
</body></html>
"""

@app.route("/")
def index():
    size = os.path.getsize(PCAP_PATH) if os.path.exists(PCAP_PATH) else 0
    return render_template_string(TEMPLATE, size=f"{size:,}")

@app.route("/download")
def download():
    return send_file(PCAP_PATH, as_attachment=True, download_name="capture.pcap")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
