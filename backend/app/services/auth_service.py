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

        user_role_str = data.role.value if hasattr(data.role, 'value') else str(data.role)
        is_domestic = (data.setup_path == "SOLO")

        # Path ① Safety Rule: If Child registering in SOLO/Domestic danger mode,
        # ensure email does not belong to any adult or guardian
        if user_role_str == "child" and is_domestic:
            adult_check = await self.db.execute(select(User).where(User.email == data.email, User.role == "adult"))
            if adult_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="For your safety, solo domestic safety registration requires an independent email not linked to a parent/guardian."
                )

        # Direct Location / GPS Auto-Resolution via live API
        if data.latitude is not None and data.longitude is not None and (not data.state or not data.district):
            from app.utils.india_locations import fetch_reverse_geocode_api
            geo = await fetch_reverse_geocode_api(data.latitude, data.longitude)
            if not data.state and geo.get("state"):
                data.state = geo.get("state")
            if not data.district and geo.get("district"):
                data.district = geo.get("district")
            if not data.pin_code and geo.get("pin_code"):
                data.pin_code = geo.get("pin_code")

        # Create user
        hashed_password = get_password_hash(data.password)
        user = User(
            email=data.email,
            hashed_password=hashed_password,
            full_name=data.full_name,
            role=user_role_str,
            phone=data.phone,
            language_preference=data.language_preference,
            state=data.state,
            district=data.district,
            pin_code=data.pin_code,
            latitude=data.latitude,
            longitude=data.longitude
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        protected_child_id = None
        setup_path = data.setup_path

        # Role-specific automatic profile & linkage initialization
        if user_role_str == "child":
            from datetime import date
            from app.models.child import Child, Adult, AdultChildLink
            from app.core.security import generate_protected_child_id
            from app.services.case_service import get_or_create_active_case_for_child
            from datetime import datetime

            # Calculate age if DOB provided
            age = None
            if data.date_of_birth:
                today = date.today()
                age = today.year - data.date_of_birth.year - (
                    (today.month, today.day) < (data.date_of_birth.month, data.date_of_birth.day)
                )

            # Generate Location-Encoded Protected Child ID (e.g. C-MH-MUM-XXXXX)
            protected_child_id = generate_protected_child_id(state=data.state, district=data.district)

            new_child = Child(
                user_id=user.id,
                protected_child_id=protected_child_id,
                display_name=data.full_name or "Child",
                age=age,
                date_of_birth=data.date_of_birth,
                state=data.state,
                district=data.district,
                pin_code=data.pin_code,
                school_name=data.school_name,
                grade=data.grade,
                is_domestic_safety_mode=is_domestic,
                setup_path=setup_path or ("SOLO" if is_domestic else "COLLABORATIVE"),
                linked_via_adult_email=data.linked_via_adult_email
            )
            self.db.add(new_child)
            await self.db.commit()
            await self.db.refresh(new_child)

            # Path ②: Adult-Linked registration via parent email shortcut
            if not is_domestic and data.linked_via_adult_email:
                adult_user_res = await self.db.execute(
                    select(User).where(User.email == data.linked_via_adult_email)
                )
                adult_user = adult_user_res.scalars().first()
                if adult_user:
                    adult_res = await self.db.execute(select(Adult).where(Adult.user_id == adult_user.id))
                    adult_record = adult_res.scalars().first()
                    if not adult_record:
                        adult_record = Adult(user_id=adult_user.id, phone=adult_user.phone)
                        self.db.add(adult_record)
                        await self.db.commit()
                        await self.db.refresh(adult_record)

                    # Create verified primary adult-child link on the spot
                    link = AdultChildLink(
                        adult_id=adult_record.id,
                        child_id=new_child.id,
                        relationship=data.relationship_to_child or "guardian",
                        is_primary=True,
                        is_verified=True,
                        linked_at=datetime.utcnow()
                    )
                    self.db.add(link)
                    await self.db.commit()

            # Auto-create active case and auto-assign district/state matched moderator
            case_title = "Domestic Safety Solo Onboarding" if is_domestic else "Child Safety Onboarding Case"
            case_desc = (
                "Child onboarded in Domestic Threat/Solo Mode. Guardians bypassed; direct moderator protection active."
                if is_domestic
                else "Child safety onboarding profile initialized with verified guardian linkage."
            )
            await get_or_create_active_case_for_child(
                self.db,
                child_id=new_child.id,
                title=case_title,
                description=case_desc,
                priority="high" if is_domestic else "medium"
            )

        elif user_role_str == "adult":
            from app.models.child import Adult
            emergency_contacts = []
            if data.emergency_contact_name and data.emergency_contact_phone:
                emergency_contacts.append({
                    "name": data.emergency_contact_name,
                    "phone": data.emergency_contact_phone,
                    "relationship": "Emergency Contact"
                })
            adult = Adult(
                user_id=user.id,
                phone=data.phone,
                address=data.address,
                state=data.state,
                district=data.district,
                pin_code=data.pin_code,
                emergency_contacts=emergency_contacts
            )
            self.db.add(adult)
            await self.db.commit()

        elif user_role_str == "moderator":
            from app.models.moderator import Moderator
            mod = Moderator(
                user_id=user.id,
                employee_id=data.employee_id,
                organisation=data.organisation,
                jurisdiction_state=data.jurisdiction_state or data.state,
                jurisdiction_district=data.jurisdiction_district or data.district,
                pocso_cert_number=data.pocso_cert_number,
                is_available=True
            )
            self.db.add(mod)
            await self.db.commit()

        # Generate tokens
        user_id_str = str(user.id)
        jti = str(uuid.uuid4())
        
        access_token = create_access_token({"sub": user_id_str, "role": user_role_str})
        refresh_token = create_refresh_token({"sub": user_id_str, "jti": jti})

        # Store refresh token in redis
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(f"refresh_token:{jti}", user_id_str, ex=ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user_role_str,
            user_id=user_id_str,
            protected_child_id=protected_child_id,
            is_domestic_safety_mode=is_domestic,
            setup_path=setup_path,
            state=user.state,
            district=user.district
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
        
        user_role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        access_token = create_access_token({"sub": user_id_str, "role": user_role_str})
        refresh_token = create_refresh_token({"sub": user_id_str, "jti": jti})

        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(f"refresh_token:{jti}", user_id_str, ex=ttl)

        protected_child_id = None
        is_domestic = None
        setup_path = None
        if user_role_str == "child":
            from app.models.child import Child
            c_res = await self.db.execute(select(Child).where(Child.user_id == user.id))
            c = c_res.scalar_one_or_none()
            if c:
                protected_child_id = c.protected_child_id
                is_domestic = c.is_domestic_safety_mode
                setup_path = c.setup_path

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user_role_str,
            user_id=user_id_str,
            protected_child_id=protected_child_id,
            is_domestic_safety_mode=is_domestic,
            setup_path=setup_path,
            state=user.state,
            district=user.district
        )

    async def claim_child_account(self, data) -> TokenResponse:
        from app.models.child import Child
        res = await self.db.execute(select(Child).where(Child.protected_child_id == data.protected_child_id))
        child = res.scalar_one_or_none()
        if not child:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child profile not found for this Protected Child ID")
        
        if child.user_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This child profile has already been claimed by an active account")

        # Check if email is already taken
        user_res = await self.db.execute(select(User).where(User.email == data.email))
        if user_res.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Create User for child
        hashed_pw = get_password_hash(data.password)
        user = User(
            email=data.email,
            hashed_password=hashed_pw,
            full_name=data.full_name or child.display_name,
            role="child",
            phone=data.phone,
            state=child.state,
            district=child.district,
            pin_code=child.pin_code
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Attach child record to the newly created user
        child.user_id = user.id
        await self.db.commit()

        user_id_str = str(user.id)
        jti = str(uuid.uuid4())
        access_token = create_access_token({"sub": user_id_str, "role": "child"})
        refresh_token = create_refresh_token({"sub": user_id_str, "jti": jti})
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(f"refresh_token:{jti}", user_id_str, ex=ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role="child",
            user_id=user_id_str,
            protected_child_id=child.protected_child_id,
            is_domestic_safety_mode=child.is_domestic_safety_mode,
            setup_path=child.setup_path,
            state=child.state,
            district=child.district
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
