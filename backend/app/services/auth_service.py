from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import redis.asyncio as redis
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token
)
from app.core.config import settings
from datetime import timedelta
from jose import JWTError
import uuid

class AuthService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def register(self, data: RegisterRequest) -> TokenResponse:
        # Check if email exists
        result = await self.db.execute(select(User).filter(User.email == data.email))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Create user
        hashed_password = get_password_hash(data.password)
        user = User(
            email=data.email,
            hashed_password=hashed_password,
            full_name=data.full_name,
            role=data.role,
            phone=data.phone,
            language_preference=data.language_preference
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Generate tokens
        user_id_str = str(user.id)
        jti = str(uuid.uuid4())
        
        access_token = create_access_token({"sub": user_id_str, "role": user.role.value if hasattr(user.role, 'value') else str(user.role)})
        refresh_token = create_refresh_token({"sub": user_id_str, "jti": jti})

        # Store refresh token in redis
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(f"refresh_token:{jti}", user_id_str, ex=ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=str(user.role.value if hasattr(user.role, 'value') else str(user.role)),
            user_id=user_id_str
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        result = await self.db.execute(select(User).filter(User.email == data.email))
        user = result.scalars().first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

        user_id_str = str(user.id)
        jti = str(uuid.uuid4())
        
        access_token = create_access_token({"sub": user_id_str, "role": user.role.value if hasattr(user.role, 'value') else str(user.role)})
        refresh_token = create_refresh_token({"sub": user_id_str, "jti": jti})

        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(f"refresh_token:{jti}", user_id_str, ex=ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=str(user.role.value if hasattr(user.role, 'value') else str(user.role)),
            user_id=user_id_str
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        jti = payload.get("jti")
        sub = payload.get("sub")
        
        if not jti or not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        redis_key = f"refresh_token:{jti}"
        stored_user_id = await self.redis.get(redis_key)
        
        if not stored_user_id or stored_user_id.decode('utf-8') != sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")

        result = await self.db.execute(select(User).filter(User.id == uuid.UUID(sub)))
        user = result.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        # Delete old token
        await self.redis.delete(redis_key)

        # Generate new tokens
        new_jti = str(uuid.uuid4())
        access_token = create_access_token({"sub": sub, "role": user.role.value if hasattr(user.role, 'value') else str(user.role)})
        new_refresh_token = create_refresh_token({"sub": sub, "jti": new_jti})

        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(f"refresh_token:{new_jti}", sub, ex=ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            role=str(user.role.value if hasattr(user.role, 'value') else str(user.role)),
            user_id=sub
        )

    async def logout(self, refresh_token: str, access_token: str) -> None:
        try:
            refresh_payload = decode_token(refresh_token)
            jti = refresh_payload.get("jti")
            if jti:
                await self.redis.delete(f"refresh_token:{jti}")
        except JWTError:
            pass # If invalid, just ignore for logout

        try:
            access_payload = decode_token(access_token)
            exp = access_payload.get("exp")
            if exp:
                import time
                import hashlib
                ttl = int(exp - time.time())
                if ttl > 0:
                    token_hash = hashlib.sha256(access_token.encode()).hexdigest()
                    await self.redis.set(f"blacklist:{token_hash}", "1", ex=ttl)
        except JWTError:
            pass

    async def get_current_user_from_token(self, token: str) -> User:
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        is_blacklisted = await self.redis.exists(f"blacklist:{token_hash}")
        if is_blacklisted:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

        try:
            payload = decode_token(token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
            
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        from app.core.security import is_token_revoked_by_epoch
        if await is_token_revoked_by_epoch(self.redis, payload.get("iat")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked due to emergency security re-keying")
            
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        result = await self.db.execute(select(User).filter(User.id == uuid.UUID(user_id)))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

        return user
