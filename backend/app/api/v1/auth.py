from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from app.core.dependencies import get_db, get_redis, get_current_active_user
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, AccessTokenResponse, UserProfile, MessageResponse,
    ClaimChildAccountRequest
)
from app.schemas.user import UserUpdate
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer()

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest, 
    db: AsyncSession = Depends(get_db), 
    redis_client: redis.Redis = Depends(get_redis)
):
    """Register a new user (child, adult, moderator, authority)."""
    auth_service = AuthService(db, redis_client)
    return await auth_service.register(data)

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, 
    db: AsyncSession = Depends(get_db), 
    redis_client: redis.Redis = Depends(get_redis)
):
    """Login with email and password."""
    auth_service = AuthService(db, redis_client)
    return await auth_service.login(data)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest, 
    db: AsyncSession = Depends(get_db), 
    redis_client: redis.Redis = Depends(get_redis)
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db, redis_client)
    return await auth_service.refresh(data.refresh_token)

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    data: Optional[RefreshRequest] = None,
    db: AsyncSession = Depends(get_db), 
    redis_client: redis.Redis = Depends(get_redis)
):
    """Logout: blacklist current tokens."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    access_token = auth_header.split(" ")[1]
    
    auth_service = AuthService(db, redis_client)
    refresh_token_str = data.refresh_token if data else ""
    await auth_service.logout(refresh_token_str, access_token)
    return MessageResponse(message="Successfully logged out")

@router.post("/claim-child-account", response_model=TokenResponse)
async def claim_child_account(
    data: ClaimChildAccountRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Claim an adult-initiated child profile and create user credentials for child."""
    auth_service = AuthService(db, redis_client)
    return await auth_service.claim_child_account(data)

@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile."""
    protected_child_id = None
    is_domestic = None
    setup_path = None
    
    if current_user.role == "child":
        from app.models.child import Child
        from sqlalchemy import select
        c_res = await db.execute(select(Child).where(Child.user_id == current_user.id))
        child = c_res.scalar_one_or_none()
        if child:
            protected_child_id = child.protected_child_id
            is_domestic = child.is_domestic_safety_mode
            setup_path = child.setup_path

    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=str(current_user.role),
        phone=current_user.phone,
        language_preference=current_user.language_preference,
        is_active=current_user.is_active,
        state=current_user.state,
        district=current_user.district,
        pin_code=current_user.pin_code,
        protected_child_id=protected_child_id,
        is_domestic_safety_mode=is_domestic,
        setup_path=setup_path
    )

@router.put("/me", response_model=UserProfile)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone
    if data.language_preference is not None:
        current_user.language_preference = data.language_preference
    if data.fcm_token is not None:
        current_user.fcm_token = data.fcm_token
        
    await db.commit()
    await db.refresh(current_user)

    protected_child_id = None
    is_domestic = None
    setup_path = None
    if current_user.role == "child":
        from app.models.child import Child
        from sqlalchemy import select
        c_res = await db.execute(select(Child).where(Child.user_id == current_user.id))
        child = c_res.scalar_one_or_none()
        if child:
            protected_child_id = child.protected_child_id
            is_domestic = child.is_domestic_safety_mode
            setup_path = child.setup_path
    
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=str(current_user.role),
        phone=current_user.phone,
        language_preference=current_user.language_preference,
        is_active=current_user.is_active,
        state=current_user.state,
        district=current_user.district,
        pin_code=current_user.pin_code,
        protected_child_id=protected_child_id,
        is_domestic_safety_mode=is_domestic,
        setup_path=setup_path
    )
