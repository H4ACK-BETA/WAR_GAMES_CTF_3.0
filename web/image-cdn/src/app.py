"""
Image CDN — Main Flask Application
Handles image upload, processing, gallery, and admin panel.
"""
import os
import uuid
import subprocess
import hashlib
import time
from flask import (
    Flask, render_template, request, redirect,
    url_for, send_from_directory, session, flash, jsonify
)
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "cdn_s3ss10n_k3y_ch4ng3_m3!")

_BASE_DIR = os.environ.get("APP_BASE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = os.path.join(_BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(_BASE_DIR, "processed")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Admin credentials (loaded from env, same as metadata service)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "cdn_admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "S3cur3_CDN_Adm1n_2024!")


def read_flag() -> str:
    """Read flag from env or /flag file."""
    flag = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if flag:
        return flag.strip()
    try:
        with open("/flag", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "WarCTF{flag_not_configured}"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image(input_path, output_path):
    """
    Process uploaded image using ImageMagick's convert.
    VULNERABILITY: SVG files can contain external references that ImageMagick
    will fetch (SSRF via SVG xlink:href or url()).
    """
    try:
        # Resize and convert to PNG for "CDN optimization"
        result = subprocess.run(
            ["convert", input_path, "-resize", "800x800>", "-quality", "85", output_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Processing timeout"
    except Exception as e:
        return False, str(e)


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}", "error")
        return redirect(url_for("index"))

    # Generate unique filename
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{unique_id}.{ext}"
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    # Process through ImageMagick
    output_filename = f"{unique_id}.png"
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)

    success, error = process_image(input_path, output_path)
    if not success:
        flash(f"Processing failed: {error}", "error")
        return redirect(url_for("index"))

    flash("Image uploaded and processed!", "success")
    return redirect(url_for("gallery"))


@app.route("/gallery")
def gallery():
    """Show processed images."""
    images = []
    if os.path.exists(PROCESSED_FOLDER):
        images = sorted(os.listdir(PROCESSED_FOLDER), reverse=True)
    return render_template("gallery.html", images=images)


@app.route("/cdn/<filename>")
def serve_image(filename):
    """Serve processed images."""
    return send_from_directory(PROCESSED_FOLDER, filename)


@app.route("/raw/<filename>")
def serve_raw(filename):
    """Serve original uploaded file (useful for examining SVG output)."""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"), code=303)
        else:
            flash("Invalid credentials", "error")

    return render_template("admin.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard — shows the flag."""
    if not session.get("admin"):
        flash("Access denied. Login required.", "error")
        return redirect(url_for("admin_login"))

    flag = read_flag()
    return f"""
    <html>
    <head><title>CDN Admin Dashboard</title>
    <style>
        body {{ font-family: monospace; background: #1a1a2e; color: #0f0; padding: 40px; }}
        .flag {{ background: #16213e; border: 2px solid #0f0; padding: 20px; margin: 20px 0;
                 font-size: 1.5em; word-break: break-all; }}
        h1 {{ color: #e94560; }}
    </style></head>
    <body>
        <h1>CDN Admin Dashboard</h1>
        <p>Welcome, {ADMIN_USERNAME}!</p>
        <div class="flag">
            <p>System Flag:</p>
            <code>{flag}</code>
        </div>
        <p><a href="/admin/logout" style="color:#0f0;">Logout</a></p>
    </body></html>
    """


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "image-cdn"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
