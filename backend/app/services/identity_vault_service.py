from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.identity_vault import IdentityVault
from app.core.security_encryption import derive_key, encrypt_field, decrypt_field
from app.core.config import settings
from typing import Optional

class IdentityVaultService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._key = derive_key(settings.IDENTITY_VAULT_KEY)

    async def store_identity(
        self,
        protected_child_id: str,
        name: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        school: Optional[str] = None,
        guardian_info: Optional[str] = None,
    ) -> IdentityVault:
        vault = IdentityVault(protected_child_id=protected_child_id)
        
        vault.encrypted_name = encrypt_field(name, self._key)
        if phone:
            vault.encrypted_phone = encrypt_field(phone, self._key)
        if address:
            vault.encrypted_address = encrypt_field(address, self._key)
        if school:
            vault.encrypted_school = encrypt_field(school, self._key)
        if guardian_info:
            vault.encrypted_guardian_info = encrypt_field(guardian_info, self._key)
            
        self.db.add(vault)
        await self.db.commit()
        await self.db.refresh(vault)
        return vault

    async def resolve_identity(self, protected_child_id: str) -> dict:
        result = await self.db.execute(select(IdentityVault).filter(IdentityVault.protected_child_id == protected_child_id))
        vault = result.scalars().first()
        
        if not vault:
            return {}
            
        return {
            "name": decrypt_field(vault.encrypted_name, self._key) if vault.encrypted_name else None,
            "phone": decrypt_field(vault.encrypted_phone, self._key) if vault.encrypted_phone else None,
            "address": decrypt_field(vault.encrypted_address, self._key) if vault.encrypted_address else None,
            "school": decrypt_field(vault.encrypted_school, self._key) if vault.encrypted_school else None,
            "guardian_info": decrypt_field(vault.encrypted_guardian_info, self._key) if vault.encrypted_guardian_info else None,
        }

    async def update_identity(self, protected_child_id: str, **fields) -> None:
        result = await self.db.execute(select(IdentityVault).filter(IdentityVault.protected_child_id == protected_child_id))
        vault = result.scalars().first()
        
        if not vault:
            return
            
        if "name" in fields and fields["name"] is not None:
            vault.encrypted_name = encrypt_field(fields["name"], self._key)
        if "phone" in fields and fields["phone"] is not None:
            vault.encrypted_phone = encrypt_field(fields["phone"], self._key)
        if "address" in fields and fields["address"] is not None:
            vault.encrypted_address = encrypt_field(fields["address"], self._key)
        if "school" in fields and fields["school"] is not None:
            vault.encrypted_school = encrypt_field(fields["school"], self._key)
        if "guardian_info" in fields and fields["guardian_info"] is not None:
            vault.encrypted_guardian_info = encrypt_field(fields["guardian_info"], self._key)
            
        await self.db.commit()
