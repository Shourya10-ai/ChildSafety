from __future__ import annotations
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

def derive_key(master_key: str) -> bytes:
    """Derive 32-byte AES key from master key string using HKDF/SHA-256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'identity_vault'
    )
    return hkdf.derive(master_key.encode('utf-8'))

def encrypt_field(plaintext: str, key_bytes: bytes) -> bytes:
    """Encrypt a string field. Returns nonce + ciphertext + tag as bytes."""
    aesgcm = AESGCM(key_bytes)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return nonce + ciphertext

def decrypt_field(ciphertext_bytes: bytes, key_bytes: bytes) -> str:
    """Decrypt bytes back to string."""
    aesgcm = AESGCM(key_bytes)
    nonce = ciphertext_bytes[:12]
    ciphertext = ciphertext_bytes[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode('utf-8')
