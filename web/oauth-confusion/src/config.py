"""Shared configuration."""
import os


def read_flag() -> str:
    flag = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if flag:
        return flag.strip()
    try:
        with open("/flag", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        pass
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base, "flag.txt"), "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "WarCTF{flag_not_configured}"


AUTH_SERVER_PORT = 9000
CLIENT_APP_PORT = 8080
AUTH_SERVER_INTERNAL = f"http://127.0.0.1:{AUTH_SERVER_PORT}"
CLIENT_APP_URL = os.environ.get("CLIENT_URL", f"http://127.0.0.1:{CLIENT_APP_PORT}")

CLIENT_ID = "secureauth-portal"
CLIENT_SECRET = "cl13nt_s3cr3t_v3ry_s4f3"

ADMIN_CLIENT_ID = "admin-dashboard"
ADMIN_CLIENT_SECRET = "4dm1n_d4shb0ard_s3cr3t"

RSA_KEY_SIZE = 2048
JWT_ALGORITHM = "RS256"
JWT_ISSUER = "secureauth-server"

AUTH_CODE_EXPIRY = 300
ACCESS_TOKEN_EXPIRY = 3600
