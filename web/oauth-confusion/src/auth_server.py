"""
OAuth 2.0 Authorization Server
Vulnerabilities:
1. Weak redirect_uri validation (path traversal / open redirect)
2. Authorization code not bound to specific client (confusion attack)
3. No audience validation on token exchange — code issued for client A
   can be exchanged by client B
4. Token replay — no single-use enforcement on auth codes
5. JWKS publicly exposed (intended, but helps attacker craft requests)
"""
import time
import uuid
import re
import urllib.parse

import jwt
from flask import Flask, request, jsonify, redirect, render_template_string

from .config import (
    AUTH_SERVER_PORT, CLIENT_ID, CLIENT_SECRET, ADMIN_CLIENT_ID,
    ADMIN_CLIENT_SECRET, AUTH_CODE_EXPIRY, ACCESS_TOKEN_EXPIRY,
    JWT_ALGORITHM, JWT_ISSUER,
)
from .keys import get_private_key_pem, get_jwks

app = Flask(__name__)
app.secret_key = "auth_s3rv3r_s3ss10n_k3y"

# In-memory stores
users_db = {
    "admin": {"password": "sup3r_s3cur3_4dm1n_p4ss!", "role": "admin", "email": "admin@secureauth.local"},
    "guest": {"password": "guest123", "role": "user", "email": "guest@secureauth.local"},
}

# Registered OAuth clients
clients_db = {
    CLIENT_ID: {
        "secret": CLIENT_SECRET,
        "redirect_uris": [
            "http://127.0.0.1:8080/callback",
            "http://localhost:8080/callback",
        ],
        "name": "SecureAuth Portal",
        "allowed_scopes": ["openid", "profile", "email"],
    },
    ADMIN_CLIENT_ID: {
        "secret": ADMIN_CLIENT_SECRET,
        "redirect_uris": [
            "http://127.0.0.1:8080/admin/callback",
            "http://localhost:8080/admin/callback",
        ],
        "name": "Admin Dashboard",
        "allowed_scopes": ["openid", "profile", "email", "admin"],
    },
}

# Authorization codes store: code -> {client_id, user, scope, redirect_uri, exp}
auth_codes = {}

# Issued tokens (for tracking / replay detection — but we DON'T enforce it properly)
issued_tokens = {}


def validate_redirect_uri(client_id: str, redirect_uri: str) -> bool:
    """
    VULNERABILITY: Weak redirect_uri validation.
    Only checks if the registered URI is a PREFIX of the provided URI.
    This allows path traversal attacks:
      registered: http://127.0.0.1:8080/callback
      attack:     http://127.0.0.1:8080/callback/../evil-endpoint
    
    Also allows subdirectory bypasses:
      http://127.0.0.1:8080/callback?next=http://attacker.com
    """
    client = clients_db.get(client_id)
    if not client:
        return False

    for registered_uri in client["redirect_uris"]:
        # BUG: prefix matching instead of exact matching
        if redirect_uri.startswith(registered_uri):
            return True
    return False


# --- Authorization Server Endpoints ---

@app.route("/.well-known/openid-configuration")
def openid_config():
    """OpenID Connect discovery document."""
    base = request.host_url.rstrip("/")
    return jsonify({
        "issuer": JWT_ISSUER,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "userinfo_endpoint": f"{base}/userinfo",
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "scopes_supported": ["openid", "profile", "email", "admin"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
    })


@app.route("/.well-known/jwks.json")
def jwks_endpoint():
    """Public JWKS for token verification."""
    return jsonify(get_jwks())


@app.route("/authorize", methods=["GET", "POST"])
def authorize():
    """
    Authorization endpoint.
    GET: Show login form
    POST: Process login and issue authorization code
    """
    client_id = request.args.get("client_id", "")
    redirect_uri = request.args.get("redirect_uri", "")
    response_type = request.args.get("response_type", "")
    scope = request.args.get("scope", "openid profile")
    state = request.args.get("state", "")

    # Basic validation
    if response_type != "code":
        return jsonify({"error": "unsupported_response_type"}), 400

    if client_id not in clients_db:
        return jsonify({"error": "invalid_client", "message": "Unknown client_id"}), 400

    if not validate_redirect_uri(client_id, redirect_uri):
        return jsonify({"error": "invalid_redirect_uri",
                        "message": f"redirect_uri not registered for client '{client_id}'"}), 400

    if request.method == "GET":
        # Render login form
        return render_template_string(LOGIN_TEMPLATE,
            client_name=clients_db[client_id]["name"],
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
        )

    # POST: process login
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    user = users_db.get(username)
    if not user or user["password"] != password:
        return render_template_string(LOGIN_TEMPLATE,
            client_name=clients_db[client_id]["name"],
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            error="Invalid username or password",
        )

    # Issue authorization code
    code = str(uuid.uuid4())
    auth_codes[code] = {
        "client_id": client_id,  # stored but NOT enforced during exchange!
        "username": username,
        "role": user["role"],
        "scope": scope,
        "redirect_uri": redirect_uri,
        "exp": time.time() + AUTH_CODE_EXPIRY,
        "used": False,  # tracked but not enforced (replay vuln)
    }

    # Redirect back with code
    separator = "&" if "?" in redirect_uri else "?"
    redirect_url = f"{redirect_uri}{separator}code={code}"
    if state:
        redirect_url += f"&state={state}"

    return redirect(redirect_url)


@app.route("/token", methods=["POST"])
def token_endpoint():
    """
    Token endpoint — exchanges authorization code for access token.
    
    VULNERABILITY: Does NOT validate that the code was issued to the requesting client.
    A code issued for 'secureauth-portal' (user scope) can be exchanged by
    'admin-dashboard' (admin scope) and the token will include admin audience.
    
    VULNERABILITY: Auth code replay — code.used flag is set but never checked.
    """
    grant_type = request.form.get("grant_type", "")
    code = request.form.get("code", "")
    redirect_uri = request.form.get("redirect_uri", "")
    client_id = request.form.get("client_id", "")
    client_secret = request.form.get("client_secret", "")

    if grant_type != "authorization_code":
        return jsonify({"error": "unsupported_grant_type"}), 400

    # Validate client credentials
    client = clients_db.get(client_id)
    if not client or client["secret"] != client_secret:
        return jsonify({"error": "invalid_client"}), 401

    # Validate authorization code exists and not expired
    code_data = auth_codes.get(code)
    if not code_data:
        return jsonify({"error": "invalid_grant", "message": "Unknown authorization code"}), 400

    if time.time() > code_data["exp"]:
        return jsonify({"error": "invalid_grant", "message": "Authorization code expired"}), 400

    # BUG: We check redirect_uri matches what was used during authorization,
    # but we DON'T check that client_id matches who the code was issued to!
    # This allows client confusion attacks.
    
    # Mark as used (but don't actually reject reuse — vulnerability!)
    code_data["used"] = True

    # Determine token scope and audience based on the REQUESTING client, not the
    # client the code was originally issued for. This is the core vulnerability.
    # If admin-dashboard exchanges the code, the token gets admin audience.
    requested_scopes = code_data["scope"].split()
    if client_id == ADMIN_CLIENT_ID:
        # Admin client gets admin scope regardless
        if "admin" not in requested_scopes:
            requested_scopes.append("admin")
        audience = ADMIN_CLIENT_ID
    else:
        audience = CLIENT_ID

    # Issue JWT access token
    now = int(time.time())
    token_payload = {
        "iss": JWT_ISSUER,
        "sub": code_data["username"],
        "aud": audience,
        "role": code_data["role"],
        "scope": " ".join(requested_scopes),
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRY,
        "jti": str(uuid.uuid4()),
    }

    access_token = jwt.encode(token_payload, get_private_key_pem(), algorithm=JWT_ALGORITHM)

    # Also issue an ID token
    id_token_payload = {
        "iss": JWT_ISSUER,
        "sub": code_data["username"],
        "aud": client_id,
        "role": code_data["role"],
        "email": users_db[code_data["username"]]["email"],
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRY,
    }
    id_token = jwt.encode(id_token_payload, get_private_key_pem(), algorithm=JWT_ALGORITHM)

    return jsonify({
        "access_token": access_token,
        "id_token": id_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRY,
        "scope": " ".join(requested_scopes),
    })


@app.route("/userinfo")
def userinfo():
    """UserInfo endpoint — returns user profile for valid access token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "invalid_token"}), 401

    token = auth_header[7:]
    try:
        from .keys import get_public_key_pem
        payload = jwt.decode(
            token, get_public_key_pem(), algorithms=["RS256"],
            options={"verify_aud": False},  # Another weakness: no audience check
        )
    except jwt.InvalidTokenError as e:
        return jsonify({"error": "invalid_token", "message": str(e)}), 401

    username = payload.get("sub")
    user = users_db.get(username)
    if not user:
        return jsonify({"error": "user_not_found"}), 404

    return jsonify({
        "sub": username,
        "role": user["role"],
        "email": user["email"],
        "scope": payload.get("scope", ""),
    })


@app.route("/register", methods=["POST"])
def register():
    """Register a new user (for CTF convenience)."""
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if len(username) < 3 or len(password) < 4:
        return jsonify({"error": "Username (min 3) and password (min 4) required"}), 400

    if username in users_db:
        return jsonify({"error": "Username already taken"}), 409

    users_db[username] = {"password": password, "role": "user", "email": f"{username}@secureauth.local"}
    return jsonify({"message": "Registration successful", "username": username, "role": "user"})


# --- Login Template ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SecureAuth - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f23; color: #ccc;
               display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .card { background: #1a1a2e; border-radius: 12px; padding: 40px; width: 380px; }
        h2 { color: #4ecdc4; margin-bottom: 5px; }
        .subtitle { color: #666; margin-bottom: 25px; font-size: 0.9em; }
        .client-info { background: #16213e; padding: 10px; border-radius: 6px;
                       margin-bottom: 20px; font-size: 0.85em; color: #888; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #16213e;
                border: 1px solid #333; border-radius: 6px; color: #fff; }
        input:focus { outline: none; border-color: #4ecdc4; }
        button { width: 100%; padding: 12px; margin-top: 15px; background: #4ecdc4;
                 color: #0f0f23; border: none; border-radius: 6px; cursor: pointer;
                 font-weight: bold; }
        button:hover { background: #45b7aa; }
        .error { background: #4a1525; color: #e94560; padding: 10px; border-radius: 6px;
                 margin-bottom: 15px; font-size: 0.9em; }
        .hint { color: #555; font-size: 0.8em; margin-top: 15px; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔐 SecureAuth</h2>
        <p class="subtitle">Authorization Server</p>
        <div class="client-info">
            Authorizing: <strong>{{ client_name }}</strong><br>
            Scopes: {{ scope }}
        </div>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/authorize?client_id={{ client_id }}&redirect_uri={{ redirect_uri }}&response_type=code&scope={{ scope }}&state={{ state }}">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Authorize</button>
        </form>
        <p class="hint">Test account: guest / guest123</p>
    </div>
</body>
</html>
"""


def create_auth_app():
    """Factory for the auth server app."""
    return app
