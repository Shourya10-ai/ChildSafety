import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status

from app.models.child import Child
from app.models.case import Case, Incident, Report, ModeratorNote
from app.models.sos import SOSEvent
from app.schemas.intelligence import (
    TimelineEventOut, ChildSafetyTimelineResponse,
    PatternFlag, CrossCasePatternsResponse, ModeratorIntelligenceReportResponse
)

async def get_child_safety_timeline(
    db: AsyncSession,
    child_id: uuid.UUID
) -> ChildSafetyTimelineResponse:
    # 1. Fetch Child
    c_res = await db.execute(select(Child).where(Child.id == child_id))
    child = c_res.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child record not found")

    events: List[TimelineEventOut] = []

    # 2. Fetch Cases
    cases_res = await db.execute(select(Case).where(Case.child_id == child_id))
    cases = cases_res.scalars().all()
    case_ids = [c.id for c in cases]

    for c in cases:
        events.append(TimelineEventOut(
            event_type="CASE_OPENED",
            timestamp=c.created_at,
            title=f"Case Opened: {c.title}",
            description=f"Status: {c.status.upper()} | SLA Tier: {c.sla_tier}",
            severity=c.priority,
            reference_id=c.protected_case_id,
            actor_role="system"
        ))

    # 3. Fetch Incidents across all cases
    if case_ids:
        inc_res = await db.execute(select(Incident).where(Incident.case_id.in_(case_ids)))
        incidents = inc_res.scalars().all()
        for inc in incidents:
            events.append(TimelineEventOut(
                event_type="INCIDENT_RECORDED",
                timestamp=inc.created_at,
                title=f"Safety Flag: {inc.incident_type.replace('_', ' ').title()}",
                description=inc.description or "Automated safety heuristic / message monitor trigger",
                severity=inc.severity,
                reference_id=str(inc.id),
                actor_role="ai_guardrail"
            ))

    # 4. Fetch SOS Events
    sos_res = await db.execute(select(SOSEvent).where(SOSEvent.child_id == child_id))
    sos_list = sos_res.scalars().all()
    for s in sos_list:
        duress_tag = " [SILENT DURESS TRIGGER]" if getattr(s, 'is_silent_duress', False) else ""
        events.append(TimelineEventOut(
            event_type="SOS_TRIGGERED",
            timestamp=s.created_at,
            title=f"🚨 Emergency SOS Beacon Dispatched{duress_tag}",
            description=f"Status: {s.status.upper()} | Coordinates: {s.latitude}, {s.longitude}",
            severity="critical",
            reference_id=str(s.id),
            actor_role="child"
        ))

    # 5. Fetch Community / Childline Reports
    reports = []
    if case_ids:
        rep_res = await db.execute(select(Report).where(Report.case_id.in_(case_ids)))
        reports = rep_res.scalars().all()
    for r in reports:
        events.append(TimelineEventOut(
            event_type="REPORT_FILED",
            timestamp=r.created_at,
            title=f"Confidential Report: {r.reporter_type.replace('_', ' ').title()}",
            description=r.content[:120] + "..." if len(r.content) > 120 else r.content,
            severity="medium",
            reference_id=str(r.id),
            actor_role="anonymous_citizen" if r.is_anonymous else "informant"
        ))

    # Chronological sort (oldest to newest for forward trajectory)
    events.sort(key=lambda e: e.timestamp)

    return ChildSafetyTimelineResponse(
        child_id=child.id,
        protected_child_id=child.protected_child_id,
        display_name=child.display_name,
        total_events=len(events),
        events=events
    )

async def detect_cross_case_patterns(
    db: AsyncSession,
    child_id: uuid.UUID
) -> CrossCasePatternsResponse:
    # 1. Fetch Child
    c_res = await db.execute(select(Child).where(Child.id == child_id))
    child = c_res.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child record not found")

    patterns: List[PatternFlag] = []

    # 2. Gather Incidents
    cases_res = await db.execute(select(Case).where(Case.child_id == child_id))
    cases = cases_res.scalars().all()
    case_ids = [c.id for c in cases]

    incidents: List[Incident] = []
    if case_ids:
        inc_res = await db.execute(select(Incident).where(Incident.case_id.in_(case_ids)).order_by(Incident.created_at.asc()))
        incidents = inc_res.scalars().all()

    # Pattern A: Recurring Grooming Indicators
    grooming_incs = [i for i in incidents if "grooming" in i.incident_type.lower() or "sexual" in i.incident_type.lower()]
    if len(grooming_incs) >= 2:
        patterns.append(PatternFlag(
            pattern_type="RECURRING_GROOMING_THREAT",
            severity="CRITICAL",
            description=f"Detected {len(grooming_incs)} grooming or exploitative attempts across multiple interactions.",
            detected_count=len(grooming_incs),
            first_observed=grooming_incs[0].created_at,
            last_observed=grooming_incs[-1].created_at,
            statutory_relevance="POCSO Act 2012 Section 11 (Sexual Harassment) & Section 19 (Mandatory Reporting)"
        ))

    # Pattern B: Persistent Bullying / Coercion
    bullying_incs = [i for i in incidents if "bullying" in i.incident_type.lower() or "threat" in i.incident_type.lower()]
    if len(bullying_incs) >= 2:
        patterns.append(PatternFlag(
            pattern_type="PERSISTENT_BULLYING_COERCION",
            severity="HIGH",
            description=f"Identified {len(bullying_incs)} repeated cyberbullying or intimidation events.",
            detected_count=len(bullying_incs),
            first_observed=bullying_incs[0].created_at,
            last_observed=bullying_incs[-1].created_at,
            statutory_relevance="Bharatiya Nyaya Sanhita (BNS) 2023 Section 351 (Criminal Intimidation)"
        ))

    # Pattern C: SOS Surge (Multiple SOS events)
    sos_res = await db.execute(select(SOSEvent).where(SOSEvent.child_id == child_id).order_by(SOSEvent.created_at.asc()))
    sos_list = sos_res.scalars().all()
    if len(sos_list) >= 2:
        patterns.append(PatternFlag(
            pattern_type="FREQUENT_EMERGENCY_DURESS",
            severity="CRITICAL",
            description=f"Child has pressed the emergency SOS beacon {len(sos_list)} times. High acute danger.",
            detected_count=len(sos_list),
            first_observed=sos_list[0].created_at,
            last_observed=sos_list[-1].created_at,
            statutory_relevance="Juvenile Justice Act 2015 Section 27 / Immediate Child Welfare Committee Referral"
        ))

    # Pattern D: Domestic Danger Mode Activated
    if getattr(child, 'is_domestic_safety_mode', False):
        patterns.append(PatternFlag(
            pattern_type="DOMESTIC_SAFETY_BYPASS_ACTIVE",
            severity="HIGH",
            description="Child enrolled under Domestic Threat Solo Protection; guardian notifications permanently suppressed.",
            detected_count=1,
            first_observed=child.created_at,
            last_observed=datetime.utcnow(),
            statutory_relevance="Protection of Women from Domestic Violence Act / POCSO Safe Custody"
        ))

    highest_risk = "LOW"
    for p in patterns:
        if p.severity == "CRITICAL":
            highest_risk = "CRITICAL"
            break
        elif p.severity == "HIGH" and highest_risk != "CRITICAL":
            highest_risk = "HIGH"
        elif p.severity == "MEDIUM" and highest_risk in ["LOW"]:
            highest_risk = "MEDIUM"

    return CrossCasePatternsResponse(
        child_id=child.id,
        total_patterns_detected=len(patterns),
        highest_risk_level=highest_risk,
        patterns=patterns
    )

async def generate_moderator_intelligence_report(
    db: AsyncSession,
    child_id: uuid.UUID
) -> ModeratorIntelligenceReportResponse:
    patterns_resp = await detect_cross_case_patterns(db, child_id)
    
    # Tally metrics
    c_res = await db.execute(select(Child).where(Child.id == child_id))
    child = c_res.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child record not found")

    cases_res = await db.execute(select(Case).where(Case.child_id == child_id))
    cases = cases_res.scalars().all()
    active_cases = len([c for c in cases if c.status in ["open", "investigating", "escalated"]])

    sos_res = await db.execute(select(func.count(SOSEvent.id)).where(SOSEvent.child_id == child_id))
    total_sos = sos_res.scalar() or 0

    case_ids = [c.id for c in cases]
    total_incidents = 0
    if case_ids:
        inc_res = await db.execute(select(func.count(Incident.id)).where(Incident.case_id.in_(case_ids)))
        total_incidents = inc_res.scalar() or 0

    statutory_triggers = []
    if patterns_resp.highest_risk_level in ["CRITICAL", "HIGH"]:
        statutory_triggers.append("Mandatory Section 19 POCSO Filing Required")
        statutory_triggers.append("Child Welfare Committee (CWC) Section 27 Referral")
        statutory_triggers.append("Section 63 BSA 2023 Evidence Preservation Lock")

    risk_trajectory = "STABLE"
    if patterns_resp.highest_risk_level == "CRITICAL":
        risk_trajectory = "ESCALATING_CRITICAL"
    elif patterns_resp.highest_risk_level == "HIGH":
        risk_trajectory = "ELEVATED_CONCERN"

    summary_notes = (
        f"Longitudinal Intelligence Dossier for {child.display_name} ({child.protected_child_id}). "
        f"Cumulative Caseload: {len(cases)} cases ({active_cases} active), {total_sos} SOS alerts, "
        f"and {total_incidents} safety infractions. Overall Trajectory: {risk_trajectory}."
    )

    return ModeratorIntelligenceReportResponse(
        child_id=child.id,
        protected_child_id=child.protected_child_id,
        display_name=child.display_name,
        age=child.age,
        total_cases=len(cases),
        active_cases=active_cases,
        total_sos_events=total_sos,
        total_incidents=total_incidents,
        risk_trajectory=risk_trajectory,
        statutory_triggers=statutory_triggers,
        patterns=patterns_resp.patterns,
        summary_notes=summary_notes,
        generated_at=datetime.utcnow()
    )
