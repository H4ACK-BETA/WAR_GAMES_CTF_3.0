"""kub3::br34ch — Flask frontend with SSRF and path traversal."""
import os
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder="templates", static_folder="static")

K8S_API = "http://127.0.0.1:6443"
SA_TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount"
LOG_BASE = os.environ.get("LOG_BASE", "/app/logs")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    return jsonify({
        "service": "novacorp-frontend",
        "version": "2.1.3",
        "environment": "production",
        "pod": "frontend-7b9d4f8c6-x2k4m",
        "status": "healthy",
    })


@app.route("/fetch", methods=["POST"])
def fetch_url():
    """SSRF endpoint — fetches a URL from inside the pod."""
    url = request.form.get("url") or request.json.get("url", "") if request.is_json else request.form.get("url", "")

    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    if url.startswith("file://") or url.startswith("gopher://"):
        return jsonify({"error": "Protocol not supported. HTTP/HTTPS only."}), 400

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    headers = {}
    auth_header = request.headers.get("X-Forward-Auth") or request.form.get("authorization") or ""
    if request.is_json:
        auth_header = request.json.get("authorization", auth_header)
    if auth_header:
        headers["Authorization"] = auth_header

    try:
        resp = requests.get(url, headers=headers, timeout=5, verify=False)
        return jsonify({
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text,
        })
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out"}), 504
    except requests.exceptions.ConnectionError as e:
        return jsonify({"error": f"Connection failed: {str(e)[:200]}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@app.route("/debug/logs")
def debug_logs():
    """Path traversal — reads log files (LFI vulnerability)."""
    path = request.args.get("path", "")

    if not path:
        return jsonify({"error": "Missing 'path' parameter",
                        "usage": "/debug/logs?path=app.log"}), 400

    base_dir = LOG_BASE
    full_path = os.path.join(base_dir, path)

    # "Sanitization" that doesn't actually prevent traversal
    if "\x00" in path:
        return jsonify({"error": "Invalid path"}), 400

    try:
        with open(full_path, "r") as f:
            content = f.read(4096)
        return jsonify({"path": path, "content": content})
    except FileNotFoundError:
        return jsonify({"error": f"Log file not found: {path}"}), 404
    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500


@app.route("/debug/env")
def debug_env():
    """Leaks some non-sensitive env vars (breadcrumb)."""
    safe_vars = {
        "POD_NAME": "frontend-7b9d4f8c6-x2k4m",
        "POD_NAMESPACE": "production",
        "SERVICE_ACCOUNT": "frontend-sa",
        "KUBERNETES_SERVICE_HOST": "10.96.0.1",
        "KUBERNETES_SERVICE_PORT": "6443",
        "NODE_NAME": "worker-node-01",
    }
    return jsonify(safe_vars)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
