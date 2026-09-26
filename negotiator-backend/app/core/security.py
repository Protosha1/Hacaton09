# app/core/security.py
"""
Password hashing (bcrypt) and JWT token utilities.
"""
from datetime import datetime, timedelta, UTC
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# =========================
# Password hashing (bcrypt)
# =========================

def hash_password(password: str) -> str:
    """
    Hash a plain-text password with bcrypt.
    Returns a string that can be safely stored in the DB.
    """
    # bcrypt works with bytes; truncate to 72 bytes (bcrypt limit)
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """
    Check whether the given plain password matches the stored hash.
    Returns False if the user has no password (e.g. legacy test users).
    """
    if not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


# =========================
# JWT tokens
# =========================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.
    `data` typically contains {"sub": user_id}.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode a JWT token. Returns the payload dict or None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None