from __future__ import annotations
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case, Incident
from app.models.child import Child
from app.models.evidence import Evidence
from app.models.knowledge_graph import SuspectEntity, IncidentSuspectLink
from app.services.statutory_rag_service import StatutoryRAGService
from app.services.risk_engine_service import RiskEngineService
from app.schemas.copilot import (
    CaseSummaryResponse,
    CaseMilestone,
    ChildSafetyChatRequest,
    ChildSafetyChatResponse,
    StatutoryCitation
)

class LLMCopilotService:
    """
    Forensic AI Legal Copilot for Human Moderators & Child Safety Guardian.
    Permission-gated forensic synthesis, case briefing, and 24/7 child guidance.
    """

    @classmethod
    async def summarize_case(
        cls,
        db: AsyncSession,
        case_id: uuid.UUID
    ) -> CaseSummaryResponse:
        """
        Synthesizes active case data into an executive forensic summary,
        milestone timeline, suspect dossier, and statutory action plan.
        """
        case_stmt = select(Case).where(Case.id == case_id)
        case = (await db.execute(case_stmt)).scalar_one_or_none()
        if not case:
            raise ValueError(f"Case with ID {case_id} not found")

        child_stmt = select(Child).where(Child.id == case.child_id)
        child = (await db.execute(child_stmt)).scalar_one_or_none()
        child_id_str = child.protected_child_id if child else "UNKNOWN"
        is_domestic = child.is_domestic_safety_mode if child else False
        child_loc = f"{child.district or ''}, {child.state or ''}".strip(", ") if child else "National"

        # Incidents
        inc_stmt = select(Incident).where(Incident.case_id == case.id).order_by(Incident.created_at.asc())
        incidents = (await db.execute(inc_stmt)).scalars().all()
        inc_ids = [inc.id for inc in incidents]

        # Evidence
        if inc_ids:
            evi_stmt = select(Evidence).where(Evidence.incident_id.in_(inc_ids))
            evidence_items = (await db.execute(evi_stmt)).scalars().all()
        else:
            evidence_items = []

        # Suspects linked to incidents
        suspect_profiles: List[Dict[str, Any]] = []
        if inc_ids:
            links_stmt = (
                select(IncidentSuspectLink, SuspectEntity)
                .join(SuspectEntity, IncidentSuspectLink.suspect_id == SuspectEntity.id)
                .where(IncidentSuspectLink.incident_id.in_(inc_ids))
            )
            links_res = (await db.execute(links_stmt)).all()
            seen_suspects = set()
            for link, susp in links_res:
                if susp.id not in seen_suspects:
                    seen_suspects.add(susp.id)
                    suspect_profiles.append({
                        "suspect_id": str(susp.id),
                        "identifier": susp.identifier,
                        "platform": susp.platform,
                        "risk_level": susp.risk_level,
                        "modus_operandi": link.modus_operandi or "Digital solicitation / harassment",
                        "confidence_score": link.confidence_score
                    })

        # Evaluate risk
        risk_eval = await RiskEngineService.evaluate_case_risk(db, case.id)

        # Build chronological milestones
        milestones: List[CaseMilestone] = []
        for inc in incidents:
            ts_str = inc.created_at.strftime("%Y-%m-%d %H:%M UTC") if inc.created_at else None
            milestones.append(
                CaseMilestone(
                    timestamp=ts_str,
                    event_type="INCIDENT_RECORDED",
                    description=f"{inc.incident_type.upper()}: {inc.description or 'Recorded safety incident'}",
                    severity=inc.severity
                )
            )
        for evi in evidence_items:
            ts_str = evi.created_at.strftime("%Y-%m-%d %H:%M UTC") if evi.created_at else None
            milestones.append(
                CaseMilestone(
                    timestamp=ts_str,
                    event_type="EVIDENCE_SECURED",
                    description=f"Evidence artifact logged ({evi.media_type}): Hash verified under Sec 63 BSA 2023",
                    severity="medium"
                )
            )

        # Retrieve applicable statutory legal provisions via RAG
        sample_query = f"{case.title or ''} " + " ".join([inc.description or inc.incident_type for inc in incidents])
        primary_incident_type = incidents[0].incident_type if incidents else "other"
        statutory_citations = StatutoryRAGService.retrieve_provisions(sample_query, primary_incident_type, top_k=3)

        # Synthesize Executive Summary
        summary_paragraphs = [
            f"Case {case.protected_case_id} ('{case.title or 'Child Safety Concern'}') is currently classified as {case.priority.upper()} priority under status {case.status}.",
            f"The affected child ({child_id_str}) is located in {child_loc or 'Unknown Jurisdiction'}."
        ]

        if is_domestic:
            summary_paragraphs.append(
                "CRITICAL SAFEGUARD: Domestic Violence / Hostile Household mode is ACTIVE. "
                "All notifications to registered household adults are strictly suppressed under Juvenile Justice Act 2015 Sec 27."
            )

        if suspect_profiles:
            susp_desc = ", ".join([f"{s['identifier']} ({s['platform']})" for s in suspect_profiles])
            summary_paragraphs.append(f"Primary identified suspect handle(s): {susp_desc}.")

        summary_paragraphs.append(
            f"Predictive Risk Engine assessed an overall threat score of {risk_eval.composite_risk_score:.2f} ({risk_eval.threat_tier} TIER), "
            f"driven by velocity={risk_eval.factors.velocity_score:.2f} and severity={risk_eval.factors.severity_score:.2f}."
        )

        executive_summary = "\n\n".join(summary_paragraphs)

        # Recommended Action Plan
        action_plan: List[str] = []
        if risk_eval.threat_tier in ["CRITICAL", "HIGH"]:
            action_plan.append("URGENT: Initiate 15-minute emergency moderator escalation protocol.")
            action_plan.append(f"Prepare mandatory SJPU / Local Police referral docket for jurisdiction {child_loc}.")

        if is_domestic:
            action_plan.append("Schedule priority referral with District Child Welfare Committee (CWC) bypassing household guardians.")

        if suspect_profiles:
            for s in suspect_profiles:
                action_plan.append(f"Issue Section 67B IT Act / Section 91 CrPC evidence preservation notice to {s['platform']} for handle {s['identifier']}.")

        action_plan.append("Preserve all chat logs, screenshots, and metadata with cryptographic hashes for court admissibility under BSA 2023.")
        action_plan.append("Schedule 24-hour follow-up welfare check with child via confidential app channel.")

        return CaseSummaryResponse(
            case_id=case.id,
            protected_case_id=case.protected_case_id,
            case_title=case.title,
            case_priority=case.priority,
            case_status=case.status,
            child_protected_id=child_id_str,
            is_domestic_safety_mode=is_domestic,
            executive_summary=executive_summary,
            chronological_milestones=milestones,
            suspect_profiles=suspect_profiles,
            applicable_statutory_provisions=statutory_citations,
            recommended_action_plan=action_plan,
            risk_assessment={
                "composite_risk_score": risk_eval.composite_risk_score,
                "threat_tier": risk_eval.threat_tier,
                "velocity_score": risk_eval.factors.velocity_score,
                "severity_score": risk_eval.factors.severity_score,
                "predator_persistence_score": risk_eval.factors.predator_persistence_score,
                "vulnerability_score": risk_eval.factors.vulnerability_score
            },
            generated_by="ForensicLegalCopilot-Grounded-v1",
            generated_at=datetime.utcnow()
        )

    @classmethod
    async def chat_with_child(
        cls,
        db: AsyncSession,
        request: ChildSafetyChatRequest
    ) -> ChildSafetyChatResponse:
        """
        24/7 Safe, Empathetic Conversational Assistant for Children.
        Includes emergency keyword interceptor, child-safe reassurance, and SOS action prompts.
        """
        msg_clean = request.message.strip().lower()

        # Emergency keyword sets
        critical_keywords = [
            "suicide", "kill myself", "end my life", "raped", "rape", "touching my private",
            "hurting me badly", "bleeding", "locked in room", "hostage", "forced to drink"
        ]
        high_keywords = [
            "blackmail", "extort", "leak my photo", "naked photo", "private photo",
            "send money or else", "meet me alone", "stalking me outside", "threatened to kill"
        ]
        moderate_keywords = [
            "bully", "bullying", "hate me", "mean to me", "secret", "don't tell anyone",
            "scared", "uncomfortable", "creepy", "asking for pictures", "send selfie"
        ]

        is_critical = any(kw in msg_clean for kw in critical_keywords)
        is_high = any(kw in msg_clean for kw in high_keywords)
        is_moderate = any(kw in msg_clean for kw in moderate_keywords)

        if is_critical:
            distress_level = "CRITICAL"
            is_emergency = True
            suggest_sos = True
            suggest_mod = True
            reassurance = "You are not alone and you are not in trouble. We are here to help you right now."
            reply = (
                "🚨 I am so sorry you are going through this. You did NOTHING wrong, and you deserve to be completely safe.\n\n"
                "Because your safety is the most important thing right now, please do one of these things immediately:\n"
                "1. **Press the RED SOS Button** at the top of the screen to alert emergency guardians and safety responders.\n"
                "2. Call **Childline 1098** or **Emergency 112** (these calls are completely free and confidential).\n\n"
                "I am also alerting a human Safety Protector right now to join this conversation."
            )
        elif is_high:
            distress_level = "HIGH"
            is_emergency = False
            suggest_sos = True
            suggest_mod = True
            reassurance = "You are safe and nobody has the right to threaten or blackmail you."
            reply = (
                "⚠️ Thank you for telling me. First, take a deep breath: **This is NOT your fault**, and whoever is threatening or blackmailing you is breaking the law.\n\n"
                "Here is what you should do right now:\n"
                "• **Do not send them any money or more pictures.** People who make threats usually ask for more if you give in.\n"
                "• **Do not delete the chat yet**, because the messages help our safety team protect you.\n"
                "• **Block the person** on that app.\n\n"
                "Would you like me to connect you with your assigned Human Safety Protector right now?"
            )
        elif is_moderate:
            distress_level = "MODERATE"
            is_emergency = False
            suggest_sos = False
            suggest_mod = True
            reassurance = "It is always okay to say NO to anyone who makes you feel uncomfortable."
            reply = (
                "Thank you for sharing this with me. If someone is asking you to keep a secret, demanding pictures, or making you feel uneasy, you have every right to step away.\n\n"
                "💡 **Safety Golden Rule:** Real friends will never pressure you to send private photos or keep dangerous secrets from trusted adults.\n\n"
                "You can tap 'Report What Happened' anytime to file a confidential report, or talk to our live Safety Protector here."
            )
        else:
            distress_level = "NONE"
            is_emergency = False
            suggest_sos = False
            suggest_mod = False
            reassurance = "I am your 24/7 AI Safety Guardian. You can talk to me whenever you feel unsure or unsafe online."
            reply = (
                "Hello! I am your AI Safety Guardian. 🛡️\n\n"
                "I am here to help you stay safe while gaming, chatting, and using social media. "
                "If anyone online is being rude, asking personal questions, or making you uncomfortable, tell me and I will help you figure out what to do!"
            )

        return ChildSafetyChatResponse(
            reply=reply,
            detected_threat=is_critical or is_high or is_moderate,
            distress_level=distress_level,
            is_emergency=is_emergency,
            suggest_sos=suggest_sos,
            suggest_moderator_transfer=suggest_mod,
            reassurance_note=reassurance,
            created_at=datetime.utcnow()
        )
