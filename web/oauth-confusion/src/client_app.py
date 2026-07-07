"""
OAuth Client Application (Resource Server)
This is the "legitimate" application that uses OAuth for login.
It also has an admin section that requires admin-scoped tokens.
"""
import jwt
import requests as http_requests
from flask import Flask, request, redirect, session, jsonify, render_template_string

from .config import (
    CLIENT_APP_PORT, AUTH_SERVER_INTERNAL, CLIENT_ID, CLIENT_SECRET,
    ADMIN_CLIENT_ID, ADMIN_CLIENT_SECRET, JWT_ALGORITHM, JWT_ISSUER,
    read_flag,
)
from .keys import get_public_key_pem

app = Flask(__name__)
app.secret_key = "cl13nt_4pp_s3ss10n_k3y_r4nd0m"


def verify_access_token(token: str, require_admin: bool = False) -> dict | None:
    """Verify JWT access token using auth server's public key."""
    try:
        payload = jwt.decode(
            token,
            get_public_key_pem(),
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},  # Intentional: doesn't verify audience
        )
        if require_admin:
            # Check for admin scope or role
            scopes = payload.get("scope", "").split()
            role = payload.get("role", "")
            if "admin" not in scopes and role != "admin":
                return None
        return payload
    except jwt.InvalidTokenError:
        return None


# --- Routes ---

@app.route("/")
def index():
    user = session.get("user")
    return render_template_string(INDEX_TEMPLATE, user=user)


@app.route("/login")
def login():
    """Initiate OAuth flow — redirect to authorization server."""
    import uuid
    state = str(uuid.uuid4())
    session["oauth_state"] = state

    auth_url = (
        f"{AUTH_SERVER_INTERNAL}/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri=http://127.0.0.1:{CLIENT_APP_PORT}/callback"
        f"&response_type=code"
        f"&scope=openid+profile+email"
        f"&state={state}"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """OAuth callback — exchange code for token."""
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    # State validation (present but doesn't prevent the confusion attack)
    expected_state = session.get("oauth_state")
    if state and expected_state and state != expected_state:
        return jsonify({"error": "State mismatch — possible CSRF"}), 400

    # Exchange code for token
    token_response = http_requests.post(
        f"{AUTH_SERVER_INTERNAL}/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"http://127.0.0.1:{CLIENT_APP_PORT}/callback",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=5,
    )

    if token_response.status_code != 200:
        return jsonify({"error": "Token exchange failed", "details": token_response.json()}), 400

    token_data = token_response.json()
    access_token = token_data["access_token"]

    # Verify token and extract user info
    payload = verify_access_token(access_token)
    if not payload:
        return jsonify({"error": "Invalid access token"}), 400

    session["user"] = {
        "username": payload["sub"],
        "role": payload.get("role", "user"),
        "scope": payload.get("scope", ""),
    }
    session["access_token"] = access_token

    return redirect("/")


@app.route("/admin/callback")
def admin_callback():
    """
    Admin OAuth callback — for the admin-dashboard client.
    This exists as a separate endpoint that uses ADMIN_CLIENT credentials.
    VULNERABILITY: An attacker can redirect a user's auth code here by
    manipulating the redirect_uri (open redirect in auth server).
    """
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No code"}), 400

    # Exchange using ADMIN client credentials — this is the confusion!
    token_response = http_requests.post(
        f"{AUTH_SERVER_INTERNAL}/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"http://127.0.0.1:{CLIENT_APP_PORT}/admin/callback",
            "client_id": ADMIN_CLIENT_ID,
            "client_secret": ADMIN_CLIENT_SECRET,
        },
        timeout=5,
    )

    if token_response.status_code != 200:
        return jsonify({"error": "Token exchange failed", "details": token_response.json()}), 400

    token_data = token_response.json()
    access_token = token_data["access_token"]

    payload = verify_access_token(access_token, require_admin=True)
    if not payload:
        # Token doesn't have admin — but the scope was added by the token endpoint!
        # Actually verify without admin requirement to debug
        payload = verify_access_token(access_token)
        if payload:
            session["user"] = {
                "username": payload["sub"],
                "role": payload.get("role", "user"),
                "scope": payload.get("scope", ""),
            }
            session["access_token"] = access_token
            return redirect("/admin")

    session["user"] = {
        "username": payload["sub"],
        "role": "admin",  # Elevated!
        "scope": payload.get("scope", ""),
    }
    session["access_token"] = access_token
    return redirect("/admin")


@app.route("/admin")
def admin_panel():
    """Admin panel — requires admin-scoped token."""
    user = session.get("user")
    access_token = session.get("access_token")

    if not user or not access_token:
        return redirect("/login")

    # Verify token has admin scope
    payload = verify_access_token(access_token, require_admin=True)
    if not payload:
        return render_template_string(ADMIN_DENIED_TEMPLATE, user=user)

    flag = read_flag()
    return render_template_string(ADMIN_TEMPLATE, user=user, flag=flag)


@app.route("/token-debug")
def token_debug():
    """
    Debug endpoint — shows decoded token (helps player understand the token structure).
    """
    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"error": "No token in session. Login first."})

    # Decode without verification for debug display
    try:
        header = jwt.get_unverified_header(access_token)
        payload = jwt.decode(access_token, options={"verify_signature": False})
        return jsonify({
            "header": header,
            "payload": payload,
            "raw_token": access_token,
            "hint": "Notice the 'aud' and 'scope' fields. What if you could get a token with 'admin' scope?",
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/.well-known/oauth-clients")
def oauth_clients_info():
    """
    Information disclosure — lists registered OAuth clients.
    This helps the attacker discover the admin-dashboard client.
    """
    return jsonify({
        "clients": [
            {
                "client_id": CLIENT_ID,
                "name": "SecureAuth Portal",
                "redirect_uris": ["http://127.0.0.1:8080/callback"],
                "scopes": ["openid", "profile", "email"],
            },
            {
                "client_id": ADMIN_CLIENT_ID,
                "name": "Admin Dashboard",
                "redirect_uris": ["http://127.0.0.1:8080/admin/callback"],
                "scopes": ["openid", "profile", "email", "admin"],
                "note": "Internal admin client — restricted access",
            },
        ],
        "auth_server": AUTH_SERVER_INTERNAL,
    })


# --- Templates ---

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SecureAuth Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f23; color: #ccc; min-height: 100vh; }
        nav { background: #1a1a2e; padding: 15px 30px; display: flex; justify-content: space-between; }
        nav a { color: #4ecdc4; text-decoration: none; margin: 0 10px; }
        .container { max-width: 600px; margin: 60px auto; padding: 20px; }
        h1 { color: #4ecdc4; margin-bottom: 10px; }
        .card { background: #1a1a2e; padding: 25px; border-radius: 10px; margin: 20px 0; }
        .btn { display: inline-block; padding: 12px 25px; background: #4ecdc4; color: #0f0f23;
               border-radius: 6px; text-decoration: none; font-weight: bold; }
        .btn:hover { background: #45b7aa; }
        .role { color: #e94560; }
    </style>
</head>
<body>
    <nav>
        <span style="color:#fff; font-weight:bold;">🔐 SecureAuth Portal</span>
        <div>
            <a href="/">Home</a>
            <a href="/admin">Admin</a>
            <a href="/token-debug">Token Debug</a>
            <a href="/.well-known/oauth-clients">OAuth Clients</a>
            {% if user %}<a href="/logout">Logout</a>{% endif %}
        </div>
    </nav>
    <div class="container">
        {% if user %}
        <h1>Welcome, {{ user.username }}!</h1>
        <div class="card">
            <p><strong>Role:</strong> <span class="role">{{ user.role }}</span></p>
            <p><strong>Scope:</strong> {{ user.scope }}</p>
            <br>
            <a href="/admin" class="btn">Access Admin Panel →</a>
            <a href="/token-debug" class="btn" style="background:#666; margin-left:10px;">Inspect Token</a>
        </div>
        {% else %}
        <h1>SecureAuth Portal</h1>
        <p style="margin:20px 0; color:#888;">Secure OAuth 2.0 powered authentication platform.</p>
        <a href="/login" class="btn">Login with OAuth →</a>
        {% endif %}
    </div>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        body { font-family: monospace; background: #0a0a1a; color: #0f0; padding: 40px; }
        .flag { background: #111; border: 2px solid #0f0; padding: 20px; margin: 20px 0;
                font-size: 1.4em; word-break: break-all; }
        h1 { color: #4ecdc4; }
        .info { color: #888; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🏴 Admin Dashboard</h1>
    <p class="info">Logged in as: {{ user.username }} | Scope: {{ user.scope }}</p>
    <div class="flag">
        <p>[ SYSTEM FLAG ]</p>
        <code>{{ flag }}</code>
    </div>
    <p><a href="/logout" style="color:#4ecdc4;">Logout</a> | <a href="/" style="color:#4ecdc4;">Home</a></p>
</body>
</html>
"""

ADMIN_DENIED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Access Denied</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f23; color: #ccc;
               display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .card { background: #1a1a2e; padding: 40px; border-radius: 12px; text-align: center; max-width: 500px; }
        h2 { color: #e94560; margin-bottom: 15px; }
        .hint { color: #555; font-size: 0.85em; margin-top: 20px; }
        a { color: #4ecdc4; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚫 Access Denied</h2>
        <p>Your token does not have admin scope.</p>
        <p style="margin-top:10px;">Current role: <strong>{{ user.role }}</strong></p>
        <p style="margin-top:10px;">Current scope: <strong>{{ user.scope }}</strong></p>
        <p class="hint">
            Hint: The admin dashboard client has different privileges.<br>
            Check <a href="/.well-known/oauth-clients">.well-known/oauth-clients</a> for registered clients.<br>
            What if you could confuse the token endpoint about which client is requesting?
        </p>
        <p style="margin-top:20px;"><a href="/">← Back</a></p>
    </div>
</body>
</html>
"""


def create_client_app():
    """Factory for the client app."""
    return app
