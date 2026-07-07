"""File server for PCAP distribution."""
import os
from flask import Flask, send_file, render_template_string

app = Flask(__name__)
PCAP_PATH = "/app/cloud_breach.pcap"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>cl0ud::br34ch</title>
<style>
body { font-family: monospace; background: #0d1117; color: #ff7b72;
       padding: 40px; display: flex; align-items: center; justify-content: center; min-height: 90vh; }
.card { background: #161b22; border: 1px solid #ff7b72; border-radius: 8px; padding: 40px;
        max-width: 550px; text-align: center; }
h1 { color: #ff7b72; margin-bottom: 10px; }
.cluster { color: #484f58; font-family: monospace; font-size: 0.8em; margin: 15px 0; text-align: left;
           background: #0d1117; padding: 15px; border-radius: 4px; }
a { color: #58a6ff; font-size: 1.1em; text-decoration: none; border: 1px solid #58a6ff;
    padding: 10px 25px; display: inline-block; margin-top: 15px; }
a:hover { background: #58a6ff; color: #0d1117; }
.meta { color: #484f58; font-size: 0.8em; margin-top: 20px; }
</style></head>
<body>
<div class="card">
    <h1>CLUSTER COMPROMISED</h1>
    <p>prod-eks-us-east-1 - Post-incident PCAP recovered</p>
    <div class="cluster">
    kubectl get nodes<br>
    &gt; No resources found.<br><br>
    kubectl get pods -A<br>
    &gt; error: connection refused
    </div>
    <a href="/download">Download cloud_breach.pcap</a>
    <p class="meta">{{ size }} bytes | 4-minute capture window</p>
</div>
</body></html>
"""

@app.route("/")
def index():
    size = os.path.getsize(PCAP_PATH) if os.path.exists(PCAP_PATH) else 0
    return render_template_string(TEMPLATE, size=f"{size:,}")

@app.route("/download")
def download():
    return send_file(PCAP_PATH, as_attachment=True, download_name="cloud_breach.pcap")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
