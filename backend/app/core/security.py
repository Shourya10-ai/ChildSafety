from __future__ import annotations
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import string
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8')[:72], hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8')[:72], salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": int(now.timestamp()), "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": int(now.timestamp()), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

async def emergency_revoke_all_tokens(redis_client) -> int:
    """
    Emergency IR Action: Globally invalidates all active access and refresh tokens.
    Sets global token revocation epoch in Redis.
    """
    if redis_client:
        epoch = int(datetime.now(timezone.utc).timestamp())
        await redis_client.set("global_token_revocation_epoch", str(epoch))
        return epoch
    return 0

async def is_token_revoked_by_epoch(redis_client, token_iat: Optional[int]) -> bool:
    """
    Checks if a token's issuance timestamp is prior to the active emergency revocation epoch.
    """
    if redis_client and token_iat:
        epoch_str = await redis_client.get("global_token_revocation_epoch")
        if epoch_str:
            try:
                epoch = int(epoch_str)
                if token_iat < epoch:
                    return True
            except Exception:
                pass
    return False

def generate_protected_child_id() -> str:
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(8))
    return f"C{random_part}"

def generate_protected_case_id() -> str:
    random_part = ''.join(secrets.choice(string.digits) for _ in range(8))
    return f"CASE-{random_part}"

