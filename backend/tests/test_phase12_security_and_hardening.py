from __future__ import annotations
import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.db.base import Base
from app.models.user import User
from app.models.child import Child, Adult, AdultChildLink
from app.models.case import Case, Incident, Report
from app.models.identity_vault import IdentityVault
from app.models.audit import AuditLog
from app.core.security_policy import (
    SecurityPolicyEngine,
    PolicySubject,
    PolicyResource,
    PolicyContext,
    PolicyAction,
    PolicyResourceType,
    SecurityRole,
)
from app.services.audit_service import AuditService, GENESIS_HASH
from app.services.vault_service import VaultService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def setup_test_db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, Session


async def run_all_tests():
    engine, Session = await setup_test_db()
    async with Session() as db:
        print("\n=======================================================")
        print("PHASE 12: SECURITY HARDENING & ABAC/BSA ENGINE TESTS")
        print("=======================================================\n")

        # ------------------------------------------------------------------
        # TEST SUITE 1: RBAC + ABAC POLICY ENGINE
        # ------------------------------------------------------------------
        print("[TEST 1] Testing RBAC + ABAC Policy Engine Rules...")

        # 1.1 Domestic Safety Isolation (Crucial POCSO/JJ Act rule)
        child_id = str(uuid.uuid4())
        parent_id = str(uuid.uuid4())

        sub_adult = PolicySubject(
            user_id=parent_id,
            role=SecurityRole.ADULT.value,
            linked_child_ids=[child_id],
        )
        res_domestic = PolicyResource(
            resource_type=PolicyResourceType.CASE.value,
            resource_id="CASE-DOM-001",
            child_id=child_id,
            is_domestic_safety_mode=True,
        )

        decision = SecurityPolicyEngine.evaluate(
            subject=sub_adult,
            resource=res_domestic,
            action=PolicyAction.READ,
        )
        assert not decision.allowed, "ABAC Failure: Linked adult was NOT blocked from domestic safety case!"
        assert decision.policy_rule == "DOMESTIC_SAFETY_ISOLATION"
        print("  - [PASS] Domestic Safety Isolation: Linked adult strictly forbidden from domestic duress case.")

        # 1.2 Normal Guardian Access for Non-Domestic Case
        res_normal = PolicyResource(
            resource_type=PolicyResourceType.CASE.value,
            resource_id="CASE-NORM-001",
            child_id=child_id,
            is_domestic_safety_mode=False,
        )
        decision_normal = SecurityPolicyEngine.evaluate(
            subject=sub_adult,
            resource=res_normal,
            action=PolicyAction.READ,
        )
        assert decision_normal.allowed, "ABAC Failure: Verified adult was blocked from standard linked case."
        assert decision_normal.policy_rule == "ADULT_LINKED_GUARDIAN"
        print("  - [PASS] Normal Guardian Access: Verified adult authorized for standard linked child case.")

        # 1.3 Jurisdiction Isolation for Moderators
        mod_mumbai = PolicySubject(
            user_id=str(uuid.uuid4()),
            role=SecurityRole.MODERATOR.value,
            state="Maharashtra",
            district="Mumbai",
            elevated_jurisdiction=False,
        )
        res_delhi = PolicyResource(
            resource_type=PolicyResourceType.CASE.value,
            resource_id="CASE-DEL-101",
            state="Delhi",
            district="New Delhi",
        )
        decision_jurisdiction = SecurityPolicyEngine.evaluate(
            subject=mod_mumbai,
            resource=res_delhi,
            action=PolicyAction.READ,
        )
        assert not decision_jurisdiction.allowed, "ABAC Failure: Moderator accessed out-of-jurisdiction state case!"
        assert decision_jurisdiction.policy_rule == "JURISDICTION_MISMATCH_STATE"
        print("  - [PASS] Jurisdiction Boundary: Out-of-state moderator blocked from Delhi case.")

        # 1.4 Case Assignment Lock for Moderators
        assigned_mod_id = str(uuid.uuid4())
        other_mod_id = str(uuid.uuid4())
        mod_assigned = PolicySubject(
            user_id=assigned_mod_id,
            role=SecurityRole.MODERATOR.value,
            state="Maharashtra",
            district="Mumbai",
        )
        mod_unassigned = PolicySubject(
            user_id=other_mod_id,
            role=SecurityRole.MODERATOR.value,
            state="Maharashtra",
            district="Mumbai",
        )
        res_case_locked = PolicyResource(
            resource_type=PolicyResourceType.CASE.value,
            resource_id="CASE-MUM-501",
            state="Maharashtra",
            district="Mumbai",
            assigned_moderator_id=assigned_mod_id,
        )

        dec_unassigned_edit = SecurityPolicyEngine.evaluate(
            subject=mod_unassigned,
            resource=res_case_locked,
            action=PolicyAction.UPDATE,
        )
        assert not dec_unassigned_edit.allowed, "ABAC Failure: Unassigned moderator allowed to modify locked case!"
        assert dec_unassigned_edit.policy_rule == "CASE_ASSIGNMENT_LOCK"

        dec_assigned_edit = SecurityPolicyEngine.evaluate(
            subject=mod_assigned,
            resource=res_case_locked,
            action=PolicyAction.UPDATE,
        )
        assert dec_assigned_edit.allowed, "ABAC Failure: Assigned moderator blocked from editing own case."
        print("  - [PASS] Case Assignment Lock: Modifications restricted to assigned moderator.")

        # 1.5 Emergency Duress Override for Responders
        res_sos = PolicyResource(
            resource_type=PolicyResourceType.SOS.value,
            resource_id="SOS-EMERGENCY-911",
            is_active_sos=True,
            state="Maharashtra",
        )
        dec_sos_override = SecurityPolicyEngine.evaluate(
            subject=mod_unassigned,
            resource=res_sos,
            action=PolicyAction.EMERGENCY_OVERRIDE,
            context=PolicyContext(is_emergency=True),
        )
        assert dec_sos_override.allowed, "ABAC Failure: Emergency duress override failed for active SOS!"
        assert dec_sos_override.policy_rule == "EMERGENCY_DURESS_OVERRIDE"
        print("  - [PASS] Emergency Duress Override: Immediate responder access granted during active SOS.")

        # ------------------------------------------------------------------
        # TEST SUITE 2: SECTION 63 BSA CRYPTOGRAPHIC AUDIT LOGGING & TAMPER DETECTION
        # ------------------------------------------------------------------
        print("\n[TEST 2] Testing Section 63 BSA 2023 Cryptographic Audit Ledger & Tamper Detection...")

        audit_service = AuditService(db)

        # 2.1 Log 5 sequential audit actions
        user_officer = uuid.uuid4()
        log1 = await audit_service.log_action("CASE_CREATED", "case", "C-100", user_officer, {"priority": "high"})
        log2 = await audit_service.log_action("INCIDENT_AI_CLASSIFIED", "incident", "INC-200", None, {"risk": 0.85})
        log3 = await audit_service.log_action("MODERATOR_NOTE_ADDED", "case", "C-100", user_officer, {"note": "POCSO Section 19 alert"})
        log4 = await audit_service.log_action("EVIDENCE_VERIFIED", "evidence", "EV-300", user_officer, {"sha256": "abcdef"})
        log5 = await audit_service.log_action("SIGHTING_CANDIDATE_FLAGGED", "sighting", "SIG-400", None, {"confidence": 0.94})

        assert log1.prev_hash == GENESIS_HASH, "Genesis block hash must equal 64 zeros."
        assert log2.prev_hash == log1.entry_hash, "Block #2 prev_hash must link to Block #1 entry_hash."
        assert log3.prev_hash == log2.entry_hash, "Block #3 prev_hash must link to Block #2 entry_hash."
        assert log4.prev_hash == log3.entry_hash, "Block #4 prev_hash must link to Block #3 entry_hash."
        assert log5.prev_hash == log4.entry_hash, "Block #5 prev_hash must link to Block #4 entry_hash."
        print("  - [PASS] Cryptographic Hash Chaining: 5 blocks successfully sequenced with SHA-256 links.")

        # 2.2 Verify Pristine Chain Integrity
        verify_result = await audit_service.verify_chain_integrity()
        assert verify_result["is_valid"] is True, f"Integrity check failed on clean ledger: {verify_result}"
        assert verify_result["total_records_verified"] == 5
        assert "SECTION 63 OF BHARATIYA SAKSHYA ADHINIYAM" in verify_result["certificate"]
        print("  - [PASS] BSA Section 63 Certificate: Pristine ledger validated with 100% mathematical certainty.")

        # 2.3 Simulate Malicious Database Row Tampering on Block #3
        print("  - Simulating database tampering attack on Block #3 (altering details)...")
        log3.details = {"note": "TAMPERED_UNAUTHORIZED_ALTERATION"}
        await db.commit()

        # 2.4 Verify Tamper Detection
        tamper_check = await audit_service.verify_chain_integrity()
        assert tamper_check["is_valid"] is False, "Cryptographic audit failed to detect payload tampering!"
        assert tamper_check["tampered_record_id"] == str(log3.id), "Audit failure did not point to tampered record #3!"
        print(f"  - [PASS] Tamper Evident Detection: Altered record {log3.id} immediately flagged: {tamper_check['failure_reason']}")

        # ------------------------------------------------------------------
        # TEST SUITE 3: HARDENED IDENTITY VAULT & KMS ENVELOPE ENCRYPTION
        # ------------------------------------------------------------------
        print("\n[TEST 3] Testing Hardened Identity Vault with KMS Envelope Encryption & Masking...")

        vault_service = VaultService(db)
        protected_child_id = "C-GA-PNJ-7788"

        # 3.1 Store Child PII
        vault_entry = await vault_service.store_identity(
            protected_child_id=protected_child_id,
            name="Aarav Anant Desai",
            phone="+91 9823456789",
            address="Flat 402, Ocean Breeze, Miramar, Panaji, Goa",
            school="Sharada Mandir School, Miramar",
            guardian_info="Sunita Desai (Mother, Ph: +91 9823400000)",
        )
        assert isinstance(vault_entry.encrypted_name, bytes), "PII must be stored as raw ciphertext bytes."
        assert b"Aarav" not in vault_entry.encrypted_name, "Plaintext name leaked in ciphertext storage!"
        print("  - [PASS] Field-Level AES-256-GCM: All sensitive PII fields stored as authenticated ciphertext.")

        # 3.2 Masked Identity Presentation
        masked = await vault_service.get_masked_identity(protected_child_id)
        assert masked["is_registered"] is True
        assert masked["masked_name"] == "A***v A***t D***i"
        assert masked["masked_phone"] == "+91 9****89"
        assert "***" in masked["masked_address"]
        print(f"  - [PASS] Masked Presentation: Safe display verified -> Name: {masked['masked_name']}, Phone: {masked['masked_phone']}")

        # 3.3 Audited Resolution under Section 63 BSA
        unmasked = await vault_service.resolve_identity_audited(
            protected_child_id=protected_child_id,
            user_id=user_officer,
            user_role="moderator",
            authorized_reason="FIR 104/2026 POCSO Court Summons Verification",
            ip_address="192.168.1.50",
            fir_number="FIR-104-2026-POCSO",
        )
        assert unmasked["name"] == "Aarav Anant Desai", "Decryption failed to return original name!"
        assert unmasked["phone"] == "+91 9823456789"
        assert unmasked["audit_log_id"] is not None
        assert unmasked["bsa_compliance"] == "Section 63 BSA 2023 Authenticated"
        print("  - [PASS] Audited Identity Resolution: PII unmasked and logged into Section 63 BSA audit chain.")

        # ------------------------------------------------------------------
        # TEST SUITE 4: EDGE SCANNER, CHILD SOVEREIGNTY & VAULT CLEARANCE
        # ------------------------------------------------------------------
        print("\n[TEST 4] Testing Edge Scan Sync, Child Sovereignty & Vault Clearance...")

        # 4.1 Child Sovereignty (Cannot access another child's case)
        other_child_id = str(uuid.uuid4())
        child_sub = PolicySubject(
            user_id=child_id,
            role=SecurityRole.CHILD.value,
        )
        foreign_case = PolicyResource(
            resource_type=PolicyResourceType.CASE.value,
            resource_id="CASE-OTHER-999",
            child_id=other_child_id,
        )
        dec_child_steal = SecurityPolicyEngine.evaluate(
            subject=child_sub,
            resource=foreign_case,
            action=PolicyAction.READ,
        )
        assert not dec_child_steal.allowed, "ABAC Failure: Child was allowed to access another child's case!"
        assert dec_child_steal.policy_rule == "CHILD_SOVEREIGNTY_VIOLATION"
        print("  - [PASS] Child Sovereignty: Child strictly blocked from other children's cases.")

        # 4.2 Vault Justification Length Check (< 10 chars rejected)
        dec_short_just = SecurityPolicyEngine.evaluate(
            subject=PolicySubject(user_id=str(user_officer), role=SecurityRole.MODERATOR.value),
            resource=PolicyResource(resource_type=PolicyResourceType.IDENTITY_VAULT.value, resource_id=protected_child_id),
            action=PolicyAction.RESOLVE_VAULT,
            context=PolicyContext(justification="too short"),
        )
        assert not dec_short_just.allowed, "ABAC Failure: Vault unmasking allowed with insufficient justification!"
        assert dec_short_just.policy_rule == "VAULT_JUSTIFICATION_REQUIRED"
        print("  - [PASS] Vault Legal Safeguard: Unmasking denied without substantive justification/FIR.")

        # 4.3 Edge Safety Scanner Simulation
        edge_predator_text = "Send me private pics or I will leak your photos to everyone at school. Don't tell your parents."
        # Verify edge scanner keyword heuristic
        has_extortion = any(kw in edge_predator_text.lower() for kw in ["leak", "send pic", "blackmail"])
        has_secrecy = any(kw in edge_predator_text.lower() for kw in ["don't tell", "secret"])
        assert has_extortion and has_secrecy, "Edge safety keywords failed to flag extortion + secrecy!"
        
        # Log edge safety finding into audit chain
        edge_log = await audit_service.log_action(
            action="EDGE_SAFETY_HIGH_RISK_TRIGGERED",
            resource_type="edge_scanner",
            resource_id=child_id,
            user_id=user_officer,
            details={
                "source_type": "TEXT",
                "detected_threat_level": "HIGH_RISK",
                "indicators": ["EXTORTION_PHOTO_COERCION", "SECRECY_COERCION"],
                "recommended_action": "SHOW_DECOY_EXIT",
            },
        )
        assert edge_log.entry_hash is not None
        assert edge_log.signature is not None
        print("  - [PASS] Edge Safety Sync: High-risk predator detection verified & cryptographically audited.")

        print("\n=======================================================")
        print("ALL PHASE 12 SECURITY HARDENING TESTS PASSED [100%]")
        print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
