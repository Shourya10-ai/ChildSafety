from __future__ import annotations
from app.services.vault_service import VaultService, KMSProvider

# Re-export VaultService as IdentityVaultService for backwards compatibility
class IdentityVaultService(VaultService):
    pass
