# OAuth Confusion - Web Challenge (Hard+)

OAuth 2.0 client confusion / audience bypass: abuse weak token endpoint validation to escalate a regular user's auth code into an admin-scoped token.

## Quick Start (Local Testing)

```bash
pip install -r requirements.txt
FLAG="WarCTF{test}" python -m src.main
# Client App: http://localhost:8080
# Auth Server: http://localhost:9000
```

Or Docker:
```bash
docker-compose up --build
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Ports:** 8080 (Client App), 9000 (Auth Server)
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var
- **Image:** Build from Dockerfile

## Vulnerabilities (Layered)

1. **Information Disclosure** - `/.well-known/oauth-clients` reveals admin-dashboard client exists
2. **Weak redirect_uri validation** - Prefix matching allows open redirect (e.g., `/callback/../admin/callback`)
3. **Client Confusion** - Token endpoint doesn't verify auth code was issued for the requesting client
4. **No audience enforcement** - Code issued for `secureauth-portal` accepted by `admin-dashboard`
5. **Token replay** - Auth codes not single-use (tracked but not enforced)
6. **Debug endpoint** - `/token-debug` reveals token structure and hints

## Intended Solve (Client Confusion)

1. Register user → login via normal OAuth flow → get auth code
2. Discover admin-dashboard client via `/.well-known/oauth-clients`
3. Exchange the auth code at `/token` using admin-dashboard's client_id/secret
4. Token endpoint issues token with `admin` scope (audience confusion)
5. Hit `/admin/callback` with the code (replayed) → admin session → flag

## Why It's Hard+

- Requires understanding of OAuth 2.0 authorization code flow internals
- Multiple vulnerabilities must be chained (not just one exploit)
- Players must identify the token endpoint doesn't bind codes to clients
- Exploit requires manual HTTP requests (can't just click through the UI)
- Understanding JWT audience (`aud`) claim semantics

## Solve

```bash
python solve.py <host> <client_port> <auth_port>
```
