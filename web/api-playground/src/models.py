"""In-memory user database and models."""
from dataclasses import dataclass, field
from typing import Dict
import hashlib


@dataclass
class User:
    username: str
    password_hash: str
    role: str = "user"
    email: str = ""
    bio: str = ""


# In-memory store
users_db: Dict[str, User] = {}


def hash_password(password: str) -> str:
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, email: str = "") -> User | None:
    """Register a new user. Returns None if username taken."""
    if username in users_db:
        return None
    user = User(
        username=username,
        password_hash=hash_password(password),
        role="user",
        email=email,
        bio="",
    )
    users_db[username] = user
    return user


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user by username/password."""
    user = users_db.get(username)
    if user and user.password_hash == hash_password(password):
        return user
    return None


def get_user(username: str) -> User | None:
    """Fetch a user by username."""
    return users_db.get(username)


def update_user(username: str, **kwargs) -> User | None:
    """Update user fields."""
    user = users_db.get(username)
    if not user:
        return None
    for key, value in kwargs.items():
        if hasattr(user, key) and key != "username" and key != "password_hash":
            setattr(user, key, value)
    return user
