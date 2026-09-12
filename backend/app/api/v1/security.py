from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_roles
from app.models.user import User
from app.core.security_policy import (
    SecurityPolicyEngine,
    PolicySubject,
    PolicyResource,
    PolicyContext,
    PolicyAction,
    PolicyResourceType,
    SecurityRole,
)
from app.services.audit_service import AuditService
from app.services.vault_service import VaultService
from app.schemas.security import (
    PolicyEvaluationRequest,
    PolicyDecisionResponse,
    AuditChainVerificationResponse,
    VaultResolutionRequest,
    VaultResolutionResponse,
    MaskedIdentityResponse,
    EdgeScanSyncRequest,
    EdgeScanSyncResponse,
)

router = APIRouter(prefix="/security", tags=["Security & BSA Forensic Audit"])


@router.post("/evaluate-policy", response_model=PolicyDecisionResponse)
async def evaluate_access_policy(
    req: PolicyEvaluationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Evaluates ABAC + RBAC policy for a given subject, resource, and action.
    Used by microservices, UI gatekeepers, and API middleware.
    """
    subject = PolicySubject(
        user_id=req.user_id,
        role=req.role,
        state=req.user_state,
        district=req.user_district,
        elevated_jurisdiction=req.elevated_jurisdiction,
        linked_child_ids=req.linked_child_ids,
        is_active_duty=True,
    )

    resource = PolicyResource(
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        child_id=req.resource_child_id,
        state=req.resource_state,
        district=req.resource_district,
        assigned_moderator_id=req.assigned_moderator_id,
        is_domestic_safety_mode=req.is_domestic_safety_mode,
        is_solo_setup=req.is_solo_setup,
        is_active_sos=req.is_active_sos,
    )

    try:
        action_enum = PolicyAction(req.action.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{req.action}'. Allowed: {[a.value for a in PolicyAction]}",
        )

    context = PolicyContext(
        is_emergency=req.is_emergency,
        justification=req.justification,
    )

    decision = SecurityPolicyEngine.evaluate(
        subject=subject,
        resource=resource,
        action=action_enum,
        context=context,
    )

    return PolicyDecisionResponse(
        allowed=decision.allowed,
        policy_rule=decision.policy_rule,
        reason=decision.reason,
        subject_role=decision.subject_role,
        resource_type=decision.resource_type,
        action=decision.action,
    )


@router.get("/audit/verify-chain", response_model=AuditChainVerificationResponse)
async def verify_audit_chain(
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "authority", "moderator")),
):
    """
    Cryptographically scans the Section 63 BSA audit ledger.
    Validates SHA-256 hash chaining and HMAC digital signatures across all blocks.
    """
    audit_service = AuditService(db)
    result = await audit_service.verify_chain_integrity(limit=limit)
    return AuditChainVerificationResponse(**result)


@router.get("/vault/masked/{protected_child_id}", response_model=MaskedIdentityResponse)
async def get_masked_child_identity(
    protected_child_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "moderator", "authority", "adult")),
):
    """
    Fetches privacy-masked PII for safe display without unmasking clearance.
    """
    vault_service = VaultService(db)
    masked = await vault_service.get_masked_identity(protected_child_id)
    if not masked.get("is_registered"):
        raise HTTPException(status_code=404, detail="Child identity not found in vault")
    return MaskedIdentityResponse(**masked)


@router.post("/vault/resolve", response_model=VaultResolutionResponse)
async def resolve_vault_identity(
    req: VaultResolutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "authority", "moderator")),
):
    """
    Unmasks real-world child PII with mandatory legal justification and Section 63 BSA audit logging.
    """
    client_ip = request.client.host if request.client else None
    vault_service = VaultService(db)

    # Policy evaluation check
    subject = PolicySubject(
        user_id=str(current_user.id),
        role=current_user.role,
        is_active_duty=current_user.is_active,
    )
    resource = PolicyResource(
        resource_type="identity_vault",
        resource_id=req.protected_child_id,
    )
    decision = SecurityPolicyEngine.evaluate(
        subject=subject,
        resource=resource,
        action=PolicyAction.RESOLVE_VAULT,
        context=PolicyContext(justification=req.authorized_reason, fir_number=req.fir_number),
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason)

    resolved = await vault_service.resolve_identity_audited(
        protected_child_id=req.protected_child_id,
        user_id=current_user.id,
        user_role=current_user.role,
        authorized_reason=req.authorized_reason,
        ip_address=client_ip,
        fir_number=req.fir_number,
    )

    if "error" in resolved:
        raise HTTPException(status_code=404, detail=resolved["error"])

    return VaultResolutionResponse(
        protected_child_id=resolved["protected_child_id"],
        name=resolved["name"],
        phone=resolved["phone"],
        address=resolved["address"],
        school=resolved["school"],
        guardian_info=resolved["guardian_info"],
        audit_log_id=resolved["audit_log_id"],
        entry_hash=resolved["entry_hash"],
        bsa_compliance=resolved["bsa_compliance"],
    )


@router.post("/edge-scan", response_model=EdgeScanSyncResponse)
async def sync_edge_scan_result(
    req: EdgeScanSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Syncs and validates on-device edge AI/OCR safety findings from the Android client.
    Creates a Section 63 BSA audit trail for high-threat edge triggers.
    """
    audit_service = AuditService(db)
    is_high_risk = req.detected_threat_level in ["HIGH_RISK", "CRITICAL"]

    audit_entry = None
    if is_high_risk:
        audit_entry = await audit_service.log_action(
            action="EDGE_SAFETY_HIGH_RISK_TRIGGERED",
            resource_type="edge_scanner",
            resource_id=req.child_id,
            user_id=current_user.id,
            details={
                "source_type": req.source_type,
                "detected_threat_level": req.detected_threat_level,
                "indicators": req.detected_indicators,
                "recommended_action": req.recommended_action,
            },
        )

    server_score = 0.92 if is_high_risk else (0.55 if req.detected_threat_level == "SUSPICIOUS" else 0.05)
    intervention = (
        "PROACTIVE_DECOY_AND_MODERATOR_NOTIFY"
        if is_high_risk
        else ("ADVICE_CHIP" if req.detected_threat_level == "SUSPICIOUS" else "NONE")
    )

    return EdgeScanSyncResponse(
        status="PROCESSED",
        child_id=req.child_id,
        edge_risk_acknowledged=True,
        server_risk_score=server_score,
        recommended_intervention=intervention,
        audit_chain_hash=audit_entry.entry_hash if audit_entry else None,
    )
