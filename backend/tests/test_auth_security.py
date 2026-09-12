from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pydantic import ValidationError
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token,
    generate_protected_child_id, generate_protected_case_id
)
from app.core.security_encryption import derive_key, encrypt_field, decrypt_field
from app.schemas.auth import RegisterRequest, UserRole

def test_password_hashing():
    pwd = "SecurePassword123"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False

def test_jwt_tokens():
    payload = {"sub": "user-uuid-1234", "role": "child"}
    token = create_access_token(payload)
    assert token is not None
    
    decoded = decode_token(token)
    assert decoded["sub"] == "user-uuid-1234"
    assert decoded["role"] == "child"
    assert decoded["type"] == "access"
    assert "exp" in decoded

def test_refresh_token():
    payload = {"sub": "user-uuid-1234", "jti": "refresh-jti-5678"}
    token = create_refresh_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user-uuid-1234"
    assert decoded["jti"] == "refresh-jti-5678"
    assert decoded["type"] == "refresh"

def test_protected_ids():
    child_id = generate_protected_child_id()
    assert child_id.startswith("C")
    assert len(child_id) == 9 # 'C' + 8 chars
    
    case_id = generate_protected_case_id()
    assert case_id.startswith("CASE-")
    assert len(case_id) == 13 # 'CASE-' + 8 digits

def test_aes_gcm_encryption_roundtrip():
    key = derive_key("test_master_key_32_characters_long_1234")
    original_text = "Aarav Sharma, St. Mary's School, New Delhi"
    
    encrypted_bytes = encrypt_field(original_text, key)
    assert encrypted_bytes != original_text.encode('utf-8')
    assert len(encrypted_bytes) > 12 # Has nonce + ciphertext + tag
    
    decrypted_text = decrypt_field(encrypted_bytes, key)
    assert decrypted_text == original_text

def test_password_validation_in_schema():
    # Valid password
    req = RegisterRequest(
        email="child@test.com",
        password="ValidPass123",
        full_name="Aarav",
        role=UserRole.CHILD
    )
    assert req.password == "ValidPass123"

    # Too short
    failed = False
    try:
        RegisterRequest(
            email="child@test.com",
            password="Short1",
            full_name="Aarav",
            role=UserRole.CHILD
        )
    except ValidationError:
        failed = True
    assert failed, "Should have failed for short password"

    # No uppercase
    failed = False
    try:
        RegisterRequest(
            email="child@test.com",
            password="lowercaseonly123",
            full_name="Aarav",
            role=UserRole.CHILD
        )
    except ValidationError:
        failed = True
    assert failed, "Should have failed for missing uppercase"

    # No digit
    failed = False
    try:
        RegisterRequest(
            email="child@test.com",
            password="NoDigitsHerePass",
            full_name="Aarav",
            role=UserRole.CHILD
        )
    except ValidationError:
        failed = True
    assert failed, "Should have failed for missing digit"

if __name__ == "__main__":
    test_password_hashing()
    test_jwt_tokens()
    test_refresh_token()
    test_protected_ids()
    test_aes_gcm_encryption_roundtrip()
    test_password_validation_in_schema()
    print("All Phase 2 security unit tests passed successfully!")
