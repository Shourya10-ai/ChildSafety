from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.case import Case, ModeratorNote
from app.models.moderator import Moderator, Assignment
from app.models.notification import Notification
from app.models.user import User

# SLA Durations in Minutes
SLA_DURATIONS: Dict[str, int] = {
    "EMERGENCY_SOS_15MIN": 15,
    "GROOMING_CRITICAL_2HR": 120,
    "HIGH_RISK_6HR": 360,
    "STANDARD_24HR": 1440
}

def determine_sla_tier(priority: str, risk_level: Optional[str] = None) -> str:
    p_lower = (priority or "").lower()
    r_lower = (risk_level or "").lower()

    if p_lower == "critical" or r_lower == "critical":
        return "EMERGENCY_SOS_15MIN"
    elif r_lower == "high" or "grooming" in p_lower:
        return "GROOMING_CRITICAL_2HR"
    elif r_lower == "medium" or p_lower == "high":
        return "HIGH_RISK_6HR"
    return "STANDARD_24HR"

def compute_sla_deadline(tier: str, start_time: Optional[datetime] = None) -> datetime:
    base = start_time or datetime.utcnow()
    mins = SLA_DURATIONS.get(tier, 1440)
    return base + timedelta(minutes=mins)

async def apply_sla_to_case(db: AsyncSession, case: Case) -> Case:
    """
    Sets SLA tier and deadline if not already initialized.
    """
    if not case.sla_deadline:
        tier = determine_sla_tier(case.priority, case.risk_level)
        case.sla_tier = tier
        case.sla_deadline = compute_sla_deadline(tier, case.created_at or datetime.utcnow())
        await db.commit()
        await db.refresh(case)
    return case

async def check_and_enforce_case_slas(db: AsyncSession) -> Dict[str, Any]:
    """
    Scans active cases for overdue SLA deadlines, triggers automatic reassignments,
    and alerts supervisors for delinquent workflows.
    """
    now = datetime.utcnow()
    
    # 1. Fetch active cases that have not yet had SLA initialized
    uninitialized_res = await db.execute(
        select(Case).where(
            and_(
                Case.status.in_(["open", "investigating"]),
                Case.sla_deadline.is_(None)
            )
        )
    )
    uninitialized = uninitialized_res.scalars().all()
    for c in uninitialized:
        tier = determine_sla_tier(c.priority, c.risk_level)
        c.sla_tier = tier
        c.sla_deadline = compute_sla_deadline(tier, c.created_at or now)
    
    if uninitialized:
        await db.commit()

    # 2. Find breached cases
    breached_res = await db.execute(
        select(Case).where(
            and_(
                Case.status.in_(["open", "investigating"]),
                Case.sla_deadline <= now,
                Case.sla_breached == False
            )
        )
    )
    breached_cases = breached_res.scalars().all()

    escalated_count = 0
    reassigned_count = 0
    escalation_details = []

    for case in breached_cases:
        case.sla_breached = True
        case.escalation_level += 1
        escalated_count += 1

        # Log system moderator note
        sla_note = ModeratorNote(
            case_id=case.id,
            moderator_id=case.moderator_id or uuid.uuid4(),  # System escalation marker
            content=f"[SYSTEM SLA ENFORCER] Case breached {case.sla_tier} deadline. Auto-escalated to Level {case.escalation_level}.",
            note_type="sla_escalation"
        )
        db.add(sla_note)

        # Workload re-balancing: Reassign to available supervisor or moderator with lowest case load
        alt_mod_res = await db.execute(
            select(Moderator)
            .where(
                and_(
                    Moderator.is_available == True,
                    Moderator.id != case.moderator_id
                )
            )
            .order_by(Moderator.active_case_count.asc())
            .limit(1)
        )
        alt_mod = alt_mod_res.scalar_one_or_none()

        old_mod_id = case.moderator_id
        if alt_mod:
            case.moderator_id = alt_mod.id
            alt_mod.active_case_count += 1
            reassigned_count += 1

            if alt_mod.user_id:
                notif = Notification(
                    user_id=alt_mod.user_id,
                    notification_type="case_escalated_sla",
                    title=f"⚠️ SLA BREACH REASSIGNMENT: Case {case.protected_case_id}",
                    body=f"Case {case.protected_case_id} breached {case.sla_tier} SLA and has been auto-reassigned to you for immediate action.",
                    data={"case_id": str(case.id), "sla_tier": case.sla_tier, "escalation_level": case.escalation_level}
                )
                db.add(notif)

        escalation_details.append({
            "case_id": str(case.id),
            "protected_case_id": case.protected_case_id,
            "sla_tier": case.sla_tier,
            "deadline": case.sla_deadline.isoformat() if case.sla_deadline else None,
            "escalation_level": case.escalation_level,
            "previous_moderator_id": str(old_mod_id) if old_mod_id else None,
            "new_moderator_id": str(case.moderator_id) if case.moderator_id else None
        })

    await db.commit()

    return {
        "checked_at": now.isoformat(),
        "total_breached_detected": escalated_count,
        "total_reassigned": reassigned_count,
        "escalations": escalation_details
    }
