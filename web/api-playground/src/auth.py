"""JWT authentication helpers."""
import jwt
import time
import os

SECRET_KEY = os.environ.get("JWT_SECRET", "pl4ygr0und_s3cr3t_k3y_d0nt_l34k!")
ALGORITHM = "HS256"
TOKEN_EXPIRY = 3600  # 1 hour


def create_token(username: str, role: str = "user") -> str:
    """Create a JWT token for a user."""
    payload = {
        "sub": username,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRY,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_role_from_token(token: str) -> str | None:
    """Extract role from token."""
    payload = verify_token(token)
    if payload:
        return payload.get("role")
    return None
