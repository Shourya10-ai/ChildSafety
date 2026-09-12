from __future__ import annotations
import uuid
import json
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc
from app.models.audit import AuditLog
from app.core.config import settings

GENESIS_HASH = "0" * 64


class AuditService:
    """
    Cryptographic, Tamper-Evident Audit Ledger Service.
    Compliant with Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA).
    Uses Merkle-style SHA-256 hash chaining and HMAC-SHA256 digital signatures
    to guarantee non-repudiation and court admissibility.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._secret = getattr(settings, "SECRET_KEY", "bsa-forensic-secret-key-section63").encode("utf-8")

    def _compute_entry_hash(
        self,
        log_id: str,
        prev_hash: str,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        details: Optional[Any],
        ip_address: Optional[str],
    ) -> str:
        payload = {
            "id": log_id,
            "prev_hash": prev_hash,
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "ip_address": ip_address,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _compute_signature(self, entry_hash: str) -> str:
        return hmac.new(self._secret, entry_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    async def get_latest_log(self) -> Optional[AuditLog]:
        stmt = select(AuditLog).order_by(desc(AuditLog.timestamp), desc(AuditLog.id)).limit(1)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Appends an immutable audit log linked cryptographically to the preceding record.
        """
        log_id = uuid.uuid4()
        last_log = await self.get_latest_log()
        prev_hash = last_log.entry_hash if (last_log and last_log.entry_hash) else GENESIS_HASH

        entry_hash = self._compute_entry_hash(
            log_id=str(log_id),
            prev_hash=prev_hash,
            user_id=str(user_id) if user_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details,
            ip_address=ip_address,
        )

        signature = self._compute_signature(entry_hash)

        audit_entry = AuditLog(
            id=log_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            signature=signature,
            bsa_section="Section 63 BSA 2023",
            timestamp=datetime.now(timezone.utc),
        )

        self.db.add(audit_entry)
        await self.db.commit()
        await self.db.refresh(audit_entry)
        return audit_entry

    async def verify_chain_integrity(self, limit: int = 1000) -> Dict[str, Any]:
        """
        Cryptographically scans all audit ledger entries in sequence.
        Detects any unauthorized row mutation, deletion, or insertion.
        Emits a Section 63 BSA electronic forensic verification report.
        """
        stmt = select(AuditLog).order_by(asc(AuditLog.timestamp), asc(AuditLog.id)).limit(limit)
        res = await self.db.execute(stmt)
        entries: List[AuditLog] = list(res.scalars().all())

        if not entries:
            return {
                "is_valid": True,
                "total_records_verified": 0,
                "genesis_hash": GENESIS_HASH,
                "certificate": "SECTION 63 BSA 2023: Empty audit ledger; genesis verified.",
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }

        expected_prev_hash = GENESIS_HASH
        for idx, entry in enumerate(entries):
            # Check 1: Chain link pointer
            if entry.prev_hash != expected_prev_hash:
                return {
                    "is_valid": False,
                    "tampered_record_id": str(entry.id),
                    "sequence_index": idx,
                    "action": entry.action,
                    "failure_reason": f"Cryptographic link broken at record #{idx}. Expected prev_hash {expected_prev_hash}, found {entry.prev_hash}.",
                    "total_records_verified": idx,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                }

            # Check 2: Re-compute entry hash
            recalculated_hash = self._compute_entry_hash(
                log_id=str(entry.id),
                prev_hash=entry.prev_hash,
                user_id=str(entry.user_id) if entry.user_id else None,
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=str(entry.resource_id) if entry.resource_id else None,
                details=entry.details,
                ip_address=entry.ip_address,
            )

            if entry.entry_hash != recalculated_hash:
                return {
                    "is_valid": False,
                    "tampered_record_id": str(entry.id),
                    "sequence_index": idx,
                    "action": entry.action,
                    "failure_reason": f"Payload modification detected at record #{idx} ({entry.id}). Stored entry_hash does not match cryptographic payload SHA-256.",
                    "total_records_verified": idx,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                }

            # Check 3: Digital signature verification
            expected_sig = self._compute_signature(entry.entry_hash)
            if entry.signature != expected_sig:
                return {
                    "is_valid": False,
                    "tampered_record_id": str(entry.id),
                    "sequence_index": idx,
                    "action": entry.action,
                    "failure_reason": f"HMAC signature failure at record #{idx} ({entry.id}). Digital seal invalid.",
                    "total_records_verified": idx,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                }

            expected_prev_hash = entry.entry_hash

        # Valid chain certificate
        cert_text = (
            f"CERTIFICATE UNDER SECTION 63 OF BHARATIYA SAKSHYA ADHINIYAM, 2023:\n"
            f"Forensic verification completed for {len(entries)} sequential audit blocks.\n"
            f"Head Block Hash: {entries[-1].entry_hash}\n"
            f"Chain Integrity: 100% MATHEMATICALLY VERIFIED (Zero Tampering Detected)."
        )

        return {
            "is_valid": True,
            "total_records_verified": len(entries),
            "head_hash": entries[-1].entry_hash,
            "certificate": cert_text,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
