from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.case import Case, Incident
from app.models.child import Child, AdultChildLink
from app.models.knowledge_graph import SuspectEntity, IncidentSuspectLink
from app.schemas.risk_engine import (
    RiskFactorBreakdown,
    StatutoryCitation,
    RiskEvaluationResponse
)

class RiskEngineService:
    @staticmethod
    def _compute_threat_tier(score: float) -> str:
        if score >= 0.75:
            return "CRITICAL"
        elif score >= 0.50:
            return "HIGH"
        elif score >= 0.25:
            return "MEDIUM"
        return "LOW"

    @classmethod
    async def evaluate_case_risk(
        cls,
        db: AsyncSession,
        case_id: uuid.UUID
    ) -> RiskEvaluationResponse:
        """
        Executes a multi-factor risk assessment combining incident velocity,
        modus operandi severity, predator persistence, and child vulnerability.
        """
        stmt = select(Case).where(Case.id == case_id)
        case = (await db.execute(stmt)).scalar_one_or_none()
        if not case:
            raise ValueError(f"Case with ID {case_id} not found")

        child_stmt = select(Child).where(Child.id == case.child_id)
        child = (await db.execute(child_stmt)).scalar_one_or_none()

        inc_stmt = select(Incident).where(Incident.case_id == case.id)
        incidents = (await db.execute(inc_stmt)).scalars().all()

        # ----------------------------------------------------
        # 1. SEVERITY SCORE (Weight: 30%)
        # ----------------------------------------------------
        type_weights = {
            "sexual_abuse": 1.0,
            "csam": 1.0,
            "grooming": 0.85,
            "sextortion": 0.90,
            "physical_threat": 0.80,
            "domestic_violence": 0.85,
            "cyberbullying": 0.50,
            "harassment": 0.55,
            "other": 0.30
        }

        severity_vals = []
        for inc in incidents:
            w = type_weights.get(inc.incident_type.lower(), 0.40)
            if inc.severity == "critical":
                w = max(w, 0.95)
            elif inc.severity == "high":
                w = max(w, 0.75)
            if inc.trust_level in ("moderator_verified", "authority_confirmed"):
                w = min(w * 1.15, 1.0)
            severity_vals.append(w)

        severity_score = max(severity_vals) if severity_vals else 0.30

        # ----------------------------------------------------
        # 2. VELOCITY SCORE (Weight: 25%)
        # ----------------------------------------------------
        now = datetime.utcnow()
        inc_last_24h = sum(1 for inc in incidents if inc.created_at and (now - inc.created_at) <= timedelta(hours=24))
        inc_last_72h = sum(1 for inc in incidents if inc.created_at and (now - inc.created_at) <= timedelta(hours=72))

        if inc_last_24h >= 2:
            velocity_score = 0.95
        elif inc_last_24h == 1:
            velocity_score = 0.70
        elif inc_last_72h >= 2:
            velocity_score = 0.60
        elif len(incidents) > 1:
            velocity_score = 0.40
        else:
            velocity_score = 0.20

        # ----------------------------------------------------
        # 3. PREDATOR PERSISTENCE (Weight: 25%)
        # ----------------------------------------------------
        inc_ids = [inc.id for inc in incidents]
        links = []
        if inc_ids:
            links_stmt = select(IncidentSuspectLink).where(IncidentSuspectLink.incident_id.in_(inc_ids))
            links = (await db.execute(links_stmt)).scalars().all()

        suspect_ids = {lk.suspect_id for lk in links}
        predator_persistence = 0.30

        if suspect_ids:
            # Check if any suspect is a serial multi-victim predator
            cross_stmt = select(IncidentSuspectLink).where(IncidentSuspectLink.suspect_id.in_(suspect_ids))
            cross_links = (await db.execute(cross_stmt)).scalars().all()
            if len(cross_links) >= 3:
                predator_persistence = 0.95  # Serial multi-victim offender!
            elif len(cross_links) >= 2:
                predator_persistence = 0.80
            else:
                predator_persistence = 0.60
        elif any(inc.incident_type in ("grooming", "sextortion", "cyberbullying") for inc in incidents):
            predator_persistence = 0.50

        # ----------------------------------------------------
        # 4. CHILD VULNERABILITY (Weight: 20%)
        # ----------------------------------------------------
        vulnerability_score = 0.30
        if child:
            if child.is_domestic_safety_mode:
                vulnerability_score = max(vulnerability_score, 0.85)

            # Check if adult is linked
            adult_links_stmt = select(AdultChildLink).where(
                AdultChildLink.child_id == child.id,
                AdultChildLink.nomination_status == "APPROVED"
            )
            adult_links = (await db.execute(adult_links_stmt)).scalars().all()
            if not adult_links:
                vulnerability_score = min(vulnerability_score + 0.15, 1.0)

            # Age factor if available
            if child.date_of_birth:
                age_years = (now.date() - child.date_of_birth).days // 365
                if age_years < 12:
                    vulnerability_score = max(vulnerability_score, 0.90)
                elif age_years <= 14:
                    vulnerability_score = max(vulnerability_score, 0.70)

        # Composite Normalized Score (0.0 to 1.0)
        composite = (
            (0.30 * severity_score) +
            (0.25 * velocity_score) +
            (0.25 * predator_persistence) +
            (0.20 * vulnerability_score)
        )
        composite = round(min(max(composite, 0.0), 1.0), 3)
        threat_tier = cls._compute_threat_tier(composite)

        # Update Case record in DB
        case.risk_score = composite
        case.risk_level = threat_tier
        if threat_tier in ("HIGH", "CRITICAL") and case.priority not in ("high", "critical"):
            case.priority = threat_tier.lower()
        await db.commit()

        # ----------------------------------------------------
        # STATUTORY CITATIONS & MANDATORY ACTION ITEMS
        # ----------------------------------------------------
        citations: List[StatutoryCitation] = []
        interventions: List[str] = []

        has_grooming = any(inc.incident_type in ("grooming", "sexual_abuse", "csam", "sextortion") for inc in incidents)
        has_bullying = any(inc.incident_type in ("cyberbullying", "harassment") for inc in incidents)
        has_physical = any(inc.incident_type in ("physical_threat", "domestic_violence") for inc in incidents)

        if has_grooming:
            citations.append(StatutoryCitation(
                act="POCSO Act 2012",
                section="Section 19",
                provision="Mandatory Reporting of Child Sexual Exploitation & Grooming",
                mandatory_action="Legal duty to report immediately to Special Juvenile Police Unit (SJPU) or local police."
            ))
            citations.append(StatutoryCitation(
                act="POCSO Act 2012",
                section="Section 11",
                provision="Sexual Harassment of Child via Electronic Communication",
                mandatory_action="Preserve electronic messages, handles, and digital artifacts for forensic submission."
            ))
            interventions.append("Flag for immediate mandatory Special Juvenile Police Unit (SJPU) transmission")
            interventions.append("Generate Section 63 BSA tamper-evident evidence package")

        if has_physical:
            citations.append(StatutoryCitation(
                act="Bharatiya Nyaya Sanhita (BNS) 2023",
                section="Section 351",
                provision="Criminal Intimidation & Endangerment of Child",
                mandatory_action="Immediate dispatch of local jurisdictional protective unit."
            ))
            interventions.append("Dispatch local field safety officer for physical wellness verification")

        if has_bullying:
            citations.append(StatutoryCitation(
                act="Information Technology Act 2000",
                section="Section 67B",
                provision="Offense of Child Cyberstalking & Coercion",
                mandatory_action="Submit preservation notice to platform intermediaries (META/Telegram)."
            ))
            interventions.append("Issue automated platform intermediary evidence preservation notice")

        if child and child.is_domestic_safety_mode:
            citations.append(StatutoryCitation(
                act="Juvenile Justice Act 2015",
                section="Section 27",
                provision="Child in Need of Care and Protection (CNCP)",
                mandatory_action="Bypass hostile household guardians and notify Child Welfare Committee (CWC)."
            ))
            interventions.append("Activate stealth duress monitoring; suppress domestic household notifications")
            interventions.append("Schedule priority hearing before District Child Welfare Committee (CWC)")

        if threat_tier == "CRITICAL":
            interventions.insert(0, "URGENT ESCALATION: 15-minute emergency moderator response protocol active")

        return RiskEvaluationResponse(
            target_type="CASE",
            target_id=case.id,
            protected_id=case.protected_case_id,
            composite_risk_score=composite,
            threat_tier=threat_tier,
            factors=RiskFactorBreakdown(
                velocity_score=round(velocity_score, 2),
                severity_score=round(severity_score, 2),
                predator_persistence_score=round(predator_persistence, 2),
                vulnerability_score=round(vulnerability_score, 2)
            ),
            statutory_citations=citations,
            recommended_interventions=interventions,
            evaluated_at=datetime.utcnow()
        )

    @classmethod
    async def evaluate_child_risk(
        cls,
        db: AsyncSession,
        child_id: uuid.UUID
    ) -> RiskEvaluationResponse:
        """
        Evaluates cumulative safety posture across all active cases for a child profile.
        """
        child_stmt = select(Child).where(Child.id == child_id)
        child = (await db.execute(child_stmt)).scalar_one_or_none()
        if not child:
            raise ValueError(f"Child with ID {child_id} not found")

        cases_stmt = select(Case).where(Case.child_id == child.id)
        cases = (await db.execute(cases_stmt)).scalars().all()

        if not cases:
            return RiskEvaluationResponse(
                target_type="CHILD",
                target_id=child.id,
                protected_id=child.protected_child_id,
                composite_risk_score=0.10,
                threat_tier="LOW",
                factors=RiskFactorBreakdown(
                    velocity_score=0.10,
                    severity_score=0.10,
                    predator_persistence_score=0.10,
                    vulnerability_score=0.85 if child.is_domestic_safety_mode else 0.20
                ),
                statutory_citations=[],
                recommended_interventions=["Child safety shield active with baseline monitoring"],
                evaluated_at=datetime.utcnow()
            )

        # Evaluate the highest-risk case
        evaluations = [await cls.evaluate_case_risk(db, c.id) for c in cases]
        evaluations.sort(key=lambda e: e.composite_risk_score, reverse=True)
        top_eval = evaluations[0]

        return RiskEvaluationResponse(
            target_type="CHILD",
            target_id=child.id,
            protected_id=child.protected_child_id,
            composite_risk_score=top_eval.composite_risk_score,
            threat_tier=top_eval.threat_tier,
            factors=top_eval.factors,
            statutory_citations=top_eval.statutory_citations,
            recommended_interventions=top_eval.recommended_interventions,
            evaluated_at=datetime.utcnow()
        )
