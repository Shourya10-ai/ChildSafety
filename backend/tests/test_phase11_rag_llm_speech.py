from __future__ import annotations
import os
import sys
import uuid
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.models.user import User
from app.models.child import Child
from app.models.case import Case, Incident, Report
from app.models.evidence import Evidence
from app.models.knowledge_graph import SuspectEntity, IncidentSuspectLink
from app.schemas.copilot import StatutoryQueryRequest, ChildSafetyChatRequest
from app.services.statutory_rag_service import StatutoryRAGService
from app.services.llm_copilot_service import LLMCopilotService
from app.services.speech_service import SpeechService

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
        print("PHASE 11: RAG, LLM COPILOT & SPEECH PIPELINE TESTS")
        print("=======================================================\n")

        # --- SEEDING BASE DATA ---
        u1 = User(email="child_rag@test.com", hashed_password="hash", full_name="Ishaan Verma", role="child")
        u_mod = User(email="moderator_rag@test.com", hashed_password="hash", full_name="Officer Sharma", role="moderator")
        db.add_all([u1, u_mod])
        await db.flush()

        ch1 = Child(
            user_id=u1.id,
            protected_child_id="C-MH-MUM-4001",
            display_name="Ishaan",
            state="Maharashtra",
            district="Mumbai",
            is_domestic_safety_mode=True
        )
        db.add(ch1)
        await db.flush()

        c1 = Case(
            child_id=ch1.id,
            protected_case_id="CS-2026-5501",
            status="INVESTIGATING",
            priority="critical",
            title="Online Extortion & Cyber-Grooming"
        )
        db.add(c1)
        await db.flush()

        inc1 = Incident(
            case_id=c1.id,
            incident_type="grooming",
            severity="critical",
            description="Unknown user @dark_predator lured child with gaming items and demanded private photos",
            trust_level="moderator_verified"
        )
        inc2 = Incident(
            case_id=c1.id,
            incident_type="sextortion",
            severity="critical",
            description="Perpetrator threatened to leak screenshots on Instagram unless money was paid",
            trust_level="moderator_verified"
        )
        db.add_all([inc1, inc2])
        await db.flush()

        susp = SuspectEntity(
            identifier="@dark_predator",
            identifier_type="HANDLE",
            platform="Instagram",
            risk_level="CRITICAL",
            notes="Serial cyberstalking handle"
        )
        db.add(susp)
        await db.flush()

        link1 = IncidentSuspectLink(
            incident_id=inc1.id,
            suspect_id=susp.id,
            modus_operandi="Gaming currency lure followed by coercion",
            confidence_score=0.98
        )
        db.add(link1)

        evi1 = Evidence(
            incident_id=inc1.id,
            file_name="screenshot.png",
            media_type="image",
            mime_type="image/png",
            file_url="https://evidence.storage/img1.png",
            file_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size=102400
        )
        db.add(evi1)
        await db.commit()

        # ----------------------------------------------------
        # TEST 1: Statutory Legal RAG Retrieval & Verification
        # ----------------------------------------------------
        print("--- Test 1: Statutory Legal RAG Retrieval & Zero Hallucination ---")
        query1 = "Perpetrator lured child with gaming skin and asked for private photos"
        citations = StatutoryRAGService.retrieve_provisions(query1, incident_type="grooming", top_k=3)
        assert len(citations) >= 1
        statute_names = [c.statute_name for c in citations]
        assert any("POCSO" in s for s in statute_names)
        pocso_cit = next(c for c in citations if "POCSO" in c.statute_name)
        assert pocso_cit.mandatory_reporting == True
        assert pocso_cit.reporting_timeline_hours == 24
        assert "SJPU" in pocso_cit.reporting_authority
        print(f"  -> Retrieved {len(citations)} statutory provisions:")
        for c in citations:
            print(f"     * [{c.statute_name} {c.section}]: {c.title} (Mandatory: {c.mandatory_reporting}, Timeline: {c.reporting_timeline_hours}h)")
        print("  -> Statutory RAG Retrieval: PASS")

        # Test CSAM retrieval under IT Act Sec 67B
        csam_citations = StatutoryRAGService.retrieve_provisions("depicting children in sexually explicit act csam transmission", top_k=2)
        it_act_cit = next((c for c in csam_citations if "67B" in c.section), None)
        assert it_act_cit is not None
        assert it_act_cit.reporting_timeline_hours == 2
        print(f"  -> IT Act Sec 67B 2-hour mandatory escalation verified: PASS")

        # ----------------------------------------------------
        # TEST 2: Forensic Case Summarization Copilot
        # ----------------------------------------------------
        print("\n--- Test 2: Forensic Case Summarization Copilot ---")
        summary_res = await LLMCopilotService.summarize_case(db, c1.id)
        assert summary_res.case_id == c1.id
        assert summary_res.protected_case_id == "CS-2026-5501"
        assert summary_res.is_domestic_safety_mode == True
        assert len(summary_res.chronological_milestones) >= 2
        assert len(summary_res.suspect_profiles) >= 1
        assert summary_res.suspect_profiles[0]["identifier"] == "@dark_predator"
        assert len(summary_res.applicable_statutory_provisions) >= 1
        assert len(summary_res.recommended_action_plan) >= 3

        print(f"  -> Generated Case Summary for {summary_res.protected_case_id}:")
        print(f"     * Executive Summary: {summary_res.executive_summary[:120]}...")
        print(f"     * Milestones: {len(summary_res.chronological_milestones)} logged")
        print(f"     * Suspect Profile: {summary_res.suspect_profiles[0]['identifier']} on {summary_res.suspect_profiles[0]['platform']}")
        print(f"     * Action Plan Items: {len(summary_res.recommended_action_plan)}")
        print("  -> Case Summarization Copilot: PASS")

        # ----------------------------------------------------
        # TEST 3: Moderator Legal Q&A Copilot
        # ----------------------------------------------------
        print("\n--- Test 3: Moderator Legal Q&A Copilot Grounding ---")
        q_req = StatutoryQueryRequest(
            query_text="Child reported extortion and blackmail on social media, household is hostile",
            incident_type="sextortion",
            child_state="Maharashtra",
            child_district="Mumbai"
        )
        guidance = StatutoryRAGService.generate_grounded_guidance(q_req)
        assert guidance.statutory_grounded == True
        assert len(guidance.statutory_citations) >= 1
        assert guidance.mandatory_reporting_required == True
        assert "Mumbai" in guidance.grounded_guidance or "SJPU" in guidance.grounded_guidance
        print(f"  -> Generated Grounded Guidance (Mandatory: {guidance.mandatory_reporting_required}, Authority: {guidance.reporting_authority}):")
        print(f"     {guidance.grounded_guidance[:150]}...")
        print("  -> Moderator Legal Q&A Copilot: PASS")

        # ----------------------------------------------------
        # TEST 4: Child AI Safety Guardian & Guardrails
        # ----------------------------------------------------
        print("\n--- Test 4: Child AI Safety Guardian & Guardrails ---")
        # 4A: Casual / Friendly
        chat1 = await LLMCopilotService.chat_with_child(db, ChildSafetyChatRequest(message="Can you give me safety tips for Roblox?"))
        assert chat1.detected_threat == False
        assert chat1.is_emergency == False
        assert chat1.suggest_sos == False
        print(f"  -> 4A Casual query handled safely: PASS")

        # 4B: High Threat / Blackmail
        chat2 = await LLMCopilotService.chat_with_child(db, ChildSafetyChatRequest(message="Someone is blackmailing me saying they will leak my private photo"))
        assert chat2.detected_threat == True
        assert chat2.distress_level == "HIGH"
        assert chat2.suggest_sos == True
        assert chat2.suggest_moderator_transfer == True
        assert "NOT your fault" in chat2.reply or "not your fault" in chat2.reply.lower()
        print(f"  -> 4B Blackmail interceptor triggered with reassurance and transfer prompt: PASS")

        # 4C: Critical Emergency / Self-Harm
        chat3 = await LLMCopilotService.chat_with_child(db, ChildSafetyChatRequest(message="I am so scared I want to kill myself please help"))
        assert chat3.detected_threat == True
        assert chat3.is_emergency == True
        assert chat3.distress_level == "CRITICAL"
        assert chat3.suggest_sos == True
        assert "1098" in chat3.reply
        print(f"  -> 4C Critical emergency distress intercepted with 1098 & SOS guidance: PASS")

        # ----------------------------------------------------
        # TEST 5: Speech-to-Text & 1-Tap Voice Incident Reporting
        # ----------------------------------------------------
        print("\n--- Test 5: Speech-to-Text & Voice Incident Reporting ---")
        audio_payload = b"An unknown stranger is sending threats on WhatsApp and asking to meet alone after school."
        trans_res = await SpeechService.transcribe_audio(audio_payload, "voice_sample.wav")
        assert trans_res.transcript == audio_payload.decode("utf-8")
        assert trans_res.detected_threat_level in ["HIGH", "MEDIUM"]
        assert len(trans_res.detected_safety_keywords) >= 1
        print(f"  -> Audio payload transcribed: '{trans_res.transcript}' (Threat: {trans_res.detected_threat_level}): PASS")

        voice_rep_res = await SpeechService.submit_voice_report(
            db=db,
            audio_bytes=audio_payload,
            filename="incident_voice_memo.m4a",
            reporter_user_id=u1.id,
            reporter_role="child",
            child_id=ch1.id,
            platform="WhatsApp"
        )
        assert voice_rep_res.report_id is not None
        assert voice_rep_res.case_id is not None
        assert voice_rep_res.transcript == audio_payload.decode("utf-8")
        assert voice_rep_res.status in ["submitted", "triaged", "pending", "active"]
        print(f"  -> Voice Report Filed: Report ID {voice_rep_res.report_id}, Case {voice_rep_res.protected_case_id}: PASS")

        print("\n=======================================================")
        print("ALL PHASE 11 BACKEND TESTS PASSED WITH 100% SUCCESS! [PASS]")
        print("=======================================================\n")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
