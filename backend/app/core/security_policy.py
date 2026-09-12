from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List
from enum import Enum


class SecurityRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    AUTHORITY = "authority"
    ADULT = "adult"
    CHILD = "child"


class PolicyAction(str, Enum):
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    ASSIGN = "assign"
    RESOLVE_VAULT = "resolve_vault"
    EMERGENCY_OVERRIDE = "emergency_override"
    VIEW_NOTES = "view_notes"
    ADD_NOTE = "add_note"


class PolicyResourceType(str, Enum):
    CASE = "case"
    INCIDENT = "incident"
    REPORT = "report"
    CHILD_PROFILE = "child_profile"
    IDENTITY_VAULT = "identity_vault"
    CHAT = "chat"
    SOS = "sos"
    EVIDENCE = "evidence"


@dataclass
class PolicySubject:
    user_id: str
    role: str
    state: Optional[str] = None
    district: Optional[str] = None
    elevated_jurisdiction: bool = False
    linked_child_ids: List[str] = field(default_factory=list)
    is_active_duty: bool = True


@dataclass
class PolicyResource:
    resource_type: str
    resource_id: str
    child_id: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    assigned_moderator_id: Optional[str] = None
    is_domestic_safety_mode: bool = False
    is_solo_setup: bool = False
    is_active_sos: bool = False
    status: Optional[str] = None


@dataclass
class PolicyContext:
    ip_address: Optional[str] = None
    is_emergency: bool = False
    justification: Optional[str] = None
    fir_number: Optional[str] = None


@dataclass
class PolicyDecision:
    allowed: bool
    policy_rule: str
    reason: str
    subject_role: str
    resource_type: str
    action: str


class SecurityPolicyEngine:
    """
    Unified RBAC + ABAC (Attribute-Based Access Control) Engine for Child Safety Platform.
    Enforces multi-layer governance:
    1. Role hierarchy (RBAC)
    2. Geographic jurisdiction boundary (ABAC)
    3. Case assignment lock (ABAC)
    4. Domestic Safety duress boundary (ABAC)
    5. Child data sovereignty (ABAC)
    6. Section 63 BSA & POCSO emergency overrides (ABAC)
    """

    @classmethod
    def evaluate(
        cls,
        subject: PolicySubject,
        resource: PolicyResource,
        action: PolicyAction,
        context: Optional[PolicyContext] = None,
    ) -> PolicyDecision:
        context = context or PolicyContext()
        role = subject.role.lower()

        # Rule 1: Inactive duty suspension
        if not subject.is_active_duty:
            return PolicyDecision(
                allowed=False,
                policy_rule="ACCOUNT_INACTIVE",
                reason="User account is inactive or suspended from duty.",
                subject_role=role,
                resource_type=resource.resource_type,
                action=action.value,
            )

        # Rule 2: Emergency Duress Override (Active SOS takes absolute precedence for responders)
        if (context.is_emergency or resource.is_active_sos) and action in [PolicyAction.READ, PolicyAction.EMERGENCY_OVERRIDE]:
            if role in [SecurityRole.ADMIN, SecurityRole.AUTHORITY, SecurityRole.MODERATOR]:
                return PolicyDecision(
                    allowed=True,
                    policy_rule="EMERGENCY_DURESS_OVERRIDE",
                    reason="Emergency distress override active: Immediate responder access granted for active SOS.",
                    subject_role=role,
                    resource_type=resource.resource_type,
                    action=action.value,
                )

        # Rule 3: DOMESTIC SAFETY ISOLATION (Absolute Isolation: Never leak to household adults)
        if (resource.is_domestic_safety_mode or resource.is_solo_setup) and role == SecurityRole.ADULT:
            return PolicyDecision(
                allowed=False,
                policy_rule="DOMESTIC_SAFETY_ISOLATION",
                reason="Child account is under Domestic Safety / Solo Protection Mode. Guardian/Adult access is strictly prohibited under POCSO & JJ Act duress provisions.",
                subject_role=role,
                resource_type=resource.resource_type,
                action=action.value,
            )

        # Rule 4: Admin Global Superuser
        if role == SecurityRole.ADMIN:
            return PolicyDecision(
                allowed=True,
                policy_rule="ADMIN_SUPERUSER",
                reason="Admin superuser access authorized.",
                subject_role=role,
                resource_type=resource.resource_type,
                action=action.value,
            )

        # Rule 5: Child Data Sovereignty
        if role == SecurityRole.CHILD:
            # Child can only view/create their own records
            if resource.child_id and resource.child_id != subject.user_id:
                return PolicyDecision(
                    allowed=False,
                    policy_rule="CHILD_SOVEREIGNTY_VIOLATION",
                    reason="Child cannot access records or data belonging to another child.",
                    subject_role=role,
                    resource_type=resource.resource_type,
                    action=action.value,
                )
            if action in [PolicyAction.DELETE, PolicyAction.ASSIGN, PolicyAction.RESOLVE_VAULT]:
                return PolicyDecision(
                    allowed=False,
                    policy_rule="CHILD_PERMISSION_DENIED",
                    reason=f"Action '{action.value}' is restricted from child role.",
                    subject_role=role,
                    resource_type=resource.resource_type,
                    action=action.value,
                )
            return PolicyDecision(
                allowed=True,
                policy_rule="CHILD_SELF_ACCESS",
                reason="Child authorized for self-owned record access.",
                subject_role=role,
                resource_type=resource.resource_type,
                action=action.value,
            )

        # Rule 6: Adult / Guardian Boundary
        if role == SecurityRole.ADULT:
            # Adult can only view non-domestic-mode records of their linked children
            if resource.child_id and resource.child_id not in subject.linked_child_ids:
                return PolicyDecision(
                    allowed=False,
                    policy_rule="ADULT_UNLINKED_CHILD",
                    reason="Adult is not verified or linked to this child.",
                    subject_role=role,
                    resource_type=resource.resource_type,
                    action=action.value,
                )
            if action in [PolicyAction.ASSIGN, PolicyAction.RESOLVE_VAULT, PolicyAction.DELETE]:
                return PolicyDecision(
                    allowed=False,
                    policy_rule="ADULT_PRIVILEGE_RESTRICTION",
                    reason=f"Action '{action.value}' is restricted to official moderators and law enforcement.",
                    subject_role=role,
                    resource_type=resource.resource_type,
                    action=action.value,
                )
            return PolicyDecision(
                allowed=True,
                policy_rule="ADULT_LINKED_GUARDIAN",
                reason="Verified guardian access authorized for linked child.",
                subject_role=role,
                resource_type=resource.resource_type,
                action=action.value,
            )

        # Rule 7: Moderator & Authority Jurisdiction Boundary
        if role in [SecurityRole.MODERATOR, SecurityRole.AUTHORITY]:
            # Jurisdiction Check
            if not subject.elevated_jurisdiction:
                if subject.state and resource.state and subject.state.lower() != resource.state.lower():
                    return PolicyDecision(
                        allowed=False,
                        policy_rule="JURISDICTION_MISMATCH_STATE",
                        reason=f"User jurisdiction ({subject.state}) does not match resource jurisdiction ({resource.state}).",
                        subject_role=role,
                        resource_type=resource.resource_type,
                        action=action.value,
                    )
                if (
                    subject.district
                    and resource.district
                    and subject.district.lower() != resource.district.lower()
                    and role == SecurityRole.MODERATOR
                ):
                    return PolicyDecision(
                        allowed=False,
                        policy_rule="JURISDICTION_MISMATCH_DISTRICT",
                        reason=f"Moderator district ({subject.district}) does not match resource district ({resource.district}).",
                        subject_role=role,
                        resource_type=resource.resource_type,
                        action=action.value,
                    )

            # Rule 8: Moderator Case Assignment Lock
            if role == SecurityRole.MODERATOR and resource.resource_type == PolicyResourceType.CASE:
                if action == PolicyAction.ASSIGN:
                    return PolicyDecision(
                        allowed=True,
                        policy_rule="MODERATOR_CLAIM_CASE",
                        reason="Moderator authorized to self-assign or transfer case.",
                        subject_role=role,
                        resource_type=resource.resource_type,
                        action=action.value,
                    )
                if action in [PolicyAction.UPDATE, PolicyAction.ADD_NOTE, PolicyAction.WRITE]:
                    if resource.assigned_moderator_id and resource.assigned_moderator_id != subject.user_id:
                        return PolicyDecision(
                            allowed=False,
                            policy_rule="CASE_ASSIGNMENT_LOCK",
                            reason="Case is assigned to another moderator. Modifications and internal notes are locked.",
                            subject_role=role,
                            resource_type=resource.resource_type,
                            action=action.value,
                        )

            # Rule 9: Identity Vault Resolution Clearance
            if action == PolicyAction.RESOLVE_VAULT:
                if not context.justification or len(context.justification.strip()) < 10:
                    return PolicyDecision(
                        allowed=False,
                        policy_rule="VAULT_JUSTIFICATION_REQUIRED",
                        reason="Mandatory legal justification (minimum 10 characters or FIR number) required to unmask Identity Vault PII.",
                        subject_role=role,
                        resource_type=resource.resource_type,
                        action=action.value,
                    )
                return PolicyDecision(
                    allowed=True,
                    policy_rule="VAULT_RESOLUTION_AUTHORIZED",
                    reason="Official legal resolution authorized. Audit log will record justification and identity.",
                    subject_role=role,
                    resource_type=resource.resource_type,
                    action=action.value,
                )

            # Default allowed for authorized official within jurisdiction
            return PolicyDecision(
                allowed=True,
                policy_rule="OFFICIAL_JURISDICTION_ACCESS",
                reason="Official role authorized within designated jurisdiction.",
                subject_role=role,
                resource_type=resource.resource_type,
                action=action.value,
            )

        # Fallback deny
        return PolicyDecision(
            allowed=False,
            policy_rule="DEFAULT_DENY",
            reason="No explicit grant matches subject role, resource, and context.",
            subject_role=role,
            resource_type=resource.resource_type,
            action=action.value,
        )
