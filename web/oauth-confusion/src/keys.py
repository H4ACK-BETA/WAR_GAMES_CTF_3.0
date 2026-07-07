"""RSA Key management for JWT signing/verification."""
import os
import json
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


_private_key = None
_public_key = None
_jwks = None


def _generate_keys():
    """Generate RSA key pair on first use."""
    global _private_key, _public_key, _jwks

    _private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    _public_key = _private_key.public_key()

    # Build JWKS for .well-known endpoint
    pub_numbers = _public_key.public_numbers()
    n_bytes = pub_numbers.n.to_bytes((pub_numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = pub_numbers.e.to_bytes((pub_numbers.e.bit_length() + 7) // 8, "big")

    _jwks = {
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": "secureauth-key-1",
            "n": base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode(),
            "e": base64.urlsafe_b64encode(e_bytes).rstrip(b"=").decode(),
        }]
    }


def get_private_key():
    if _private_key is None:
        _generate_keys()
    return _private_key


def get_public_key():
    if _public_key is None:
        _generate_keys()
    return _public_key


def get_private_key_pem() -> bytes:
    key = get_private_key()
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_public_key_pem() -> bytes:
    key = get_public_key()
    return key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def get_jwks() -> dict:
    if _jwks is None:
        _generate_keys()
    return _jwks
