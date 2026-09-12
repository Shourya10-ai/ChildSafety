from __future__ import annotations
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum

from datetime import date

class UserRole(str, Enum):
    CHILD = "child"
    ADULT = "adult"
    MODERATOR = "moderator"
    AUTHORITY = "authority"
    ADMIN = "admin"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    language_preference: str = "en"
    
    # Common location fields (Mandatory in production flow)
    state: Optional[str] = None
    district: Optional[str] = None
    pin_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    date_of_birth: Optional[date] = None

    # Child-specific
    setup_path: Optional[str] = "COLLABORATIVE"  # "SOLO" or "COLLABORATIVE"
    school_name: Optional[str] = None
    grade: Optional[str] = None
    linked_via_adult_email: Optional[EmailStr] = None
    
    # Adult-specific
    relationship_to_child: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    # Moderator / Authority specific
    organisation: Optional[str] = None
    jurisdiction_state: Optional[str] = None
    jurisdiction_district: Optional[str] = None
    employee_id: Optional[str] = None
    pocso_cert_number: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    protected_child_id: Optional[str] = None
    is_domestic_safety_mode: Optional[bool] = None
    setup_path: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ClaimChildAccountRequest(BaseModel):
    email: EmailStr
    password: str
    protected_child_id: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    phone: Optional[str]
    language_preference: str
    is_active: bool
    state: Optional[str] = None
    district: Optional[str] = None
    pin_code: Optional[str] = None
    protected_child_id: Optional[str] = None
    is_domestic_safety_mode: Optional[bool] = None
    setup_path: Optional[str] = None
    
    model_config = {"from_attributes": True}

class MessageResponse(BaseModel):
    message: str
