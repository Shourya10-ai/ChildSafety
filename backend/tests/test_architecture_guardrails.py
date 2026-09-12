import asyncio
import os
import sys
import uuid

# Ensure backend root and workspace root are on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.models.user import User
from app.models.child import Child
from app.models.moderator import Moderator, Assignment
from app.models.case import Case, ModeratorNote, Incident, Report
from app.models.evidence import Evidence
from app.models.chain_of_custody import EvidenceChainOfCustody
from app.models.parental_consent import ParentalConsent
from app.schemas.case import CaseStatus
from app.services import case_service
from app.services import evidence_service
from app.services import consent_service
from app.core.rate_limiter import RateLimiter
from ai_server.app.rag.statutory_rag import StatutoryRAGCopilot
from ai_server.app.rag.schemas import ModeratorGuidanceQuery

# Fake redis for test environment
import fakeredis.aioredis as fake_redis

TEST_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_guardrails.db")
TEST_SQLITE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

async def run_all_guardrail_tests():
    print("Running Architecture Guardrails Automated Test Suite...")

    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    engine = create_async_engine(TEST_SQLITE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    tables = [
        User.__table__,
        Child.__table__,
        Moderator.__table__,
        Assignment.__table__,
        Case.__table__,
        Incident.__table__,
        Report.__table__,
        ModeratorNote.__table__,
        Evidence.__table__,
        EvidenceChainOfCustody.__table__,
        ParentalConsent.__table__
    ]

    async with engine.begin() as conn:
        for t in tables:
            await conn.run_sync(t.create, checkfirst=True)

    redis_client = fake_redis.FakeRedis()

    async with session_maker() as db:
        # Create test users
        child_user = User(
            email="guardrail_child@example.com",
            hashed_password="hashed_pwd_child",
            phone="+919999000111",
            role="child",
            is_active=True
        )
        mod_user = User(
            email="guardrail_mod@example.com",
            hashed_password="hashed_pwd_mod",
            phone="+919999000222",
            role="moderator",
            is_active=True
        )
        db.add_all([child_user, mod_user])
        await db.commit()
        await db.refresh(child_user)
        await db.refresh(mod_user)

        child = Child(user_id=child_user.id, protected_child_id="C9TEST01", display_name="Test Child")
        moderator = Moderator(user_id=mod_user.id, is_available=True, max_cases=10)
        db.add_all([child, moderator])
        await db.commit()
        await db.refresh(child)
        await db.refresh(moderator)

        # -------------------------------------------------------------
        # TEST 1: Human-in-the-Loop Case State Machine
        # -------------------------------------------------------------
        # 1a. Create AI-flagged case
        ai_case = Case(
            child_id=child.id,
            moderator_id=moderator.id,
            protected_case_id="CASE-AI-0001",
            status=CaseStatus.AI_FLAGGED.value,
            priority="high",
            title="Automated Grooming Risk Flag"
        )
        db.add(ai_case)
        await db.commit()
        await db.refresh(ai_case)

        # 1b. Verify that direct escalation from AI_FLAGGED is REJECTED
        direct_escalation_blocked = False
        try:
            await case_service.transition_case_status(
                db=db,
                case_id=ai_case.id,
                to_status=CaseStatus.ESCALATED,
                reason="Auto escalate",
                actor_role="system"
            )
        except Exception as e:
            if "Human-in-the-Loop Violation" in str(e):
                direct_escalation_blocked = True

        assert direct_escalation_blocked, "Direct AI escalation without human gate was NOT blocked!"

        # 1c. Moderator confirms the flag
        confirmed_case = await case_service.transition_case_status(
            db=db,
            case_id=ai_case.id,
            to_status=CaseStatus.MODERATOR_CONFIRMED,
            reason="Verified predatory grooming language in chat transcripts.",
            actor_id=moderator.id,
            actor_role="moderator",
            statutory_reference="POCSO Act Section 11"
        )
        assert confirmed_case.status == CaseStatus.MODERATOR_CONFIRMED.value

        # 1d. Now escalation is permitted because human moderator confirmed it
        escalated_case = await case_service.transition_case_status(
            db=db,
            case_id=ai_case.id,
            to_status=CaseStatus.ESCALATED,
            reason="Escalating to SJPU for immediate intervention.",
            actor_id=moderator.id,
            actor_role="moderator"
        )
        assert escalated_case.status == CaseStatus.ESCALATED.value
        print("  [OK] Human-in-the-loop state machine enforcement verified")

        # -------------------------------------------------------------
        # TEST 2: Tamper-Evident Evidence Chain of Custody
        # -------------------------------------------------------------
        evidence = Evidence(
            file_url="/storage/evidence/test_screenshot.png",
            file_name="screenshot.png",
            file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size=1024,
            media_type="image",
            mime_type="image/png"
        )
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)

        # Record Genesis block
        b1 = await evidence_service.record_chain_of_custody_event(
            db=db,
            evidence_id=evidence.id,
            action="UPLOADED",
            file_sha256=evidence.file_hash,
            actor_id=child_user.id,
            actor_role="child"
        )
        assert b1.sequence_number == 1
        assert b1.previous_block_hash == "0" * 64

        # Record Second block
        b2 = await evidence_service.record_chain_of_custody_event(
            db=db,
            evidence_id=evidence.id,
            action="VERIFIED_BY_HUMAN",
            file_sha256=evidence.file_hash,
            actor_id=mod_user.id,
            actor_role="moderator"
        )
        assert b2.sequence_number == 2
        assert b2.previous_block_hash == b1.block_hash

        # Verify intact chain
        v_intact = await evidence_service.verify_evidence_chain_of_custody(db, evidence.id)
        assert v_intact["is_valid"] is True
        assert v_intact["block_count"] == 2

        # Simulate database tampering (tamper block 1 hash)
        b1.entry_payload_hash = "f" * 64
        await db.commit()

        v_tampered = await evidence_service.verify_evidence_chain_of_custody(db, evidence.id)
        assert v_tampered["is_valid"] is False
        assert v_tampered["broken_at_sequence"] == 1
        print("  [OK] Cryptographic chain-of-custody & tamper detection verified")

        # -------------------------------------------------------------
        # TEST 3: Redis Sliding-Window Rate Limiting & Anti-Spam
        # -------------------------------------------------------------
        test_ip = "192.168.1.50"
        # 3a. Verify sliding window rate limiter
        for _ in range(3):
            await RateLimiter.check_sliding_window(
                redis_client=redis_client,
                key_prefix="test_limit",
                identifier=test_ip,
                max_requests=3,
                window_seconds=60
            )

        throttled = False
        try:
            # 4th request must fail
            await RateLimiter.check_sliding_window(
                redis_client=redis_client,
                key_prefix="test_limit",
                identifier=test_ip,
                max_requests=3,
                window_seconds=60
            )
        except Exception:
            throttled = True

        assert throttled, "4th request should have triggered HTTP 429 rate limit!"

        # 3b. Verify content deduplication
        dup_content = "Bullying message spam copy paste"
        dup_category = "cyberbullying"

        await RateLimiter.check_content_duplicate(redis_client, dup_content, dup_category, ttl_seconds=60)
        dup_blocked = False
        try:
            await RateLimiter.check_content_duplicate(redis_client, dup_content, dup_category, ttl_seconds=60)
        except Exception:
            dup_blocked = True

        assert dup_blocked, "Exact duplicate content within 15 minutes was NOT blocked!"
        print("  [OK] Sliding window rate limiter & duplicate spam prevention verified")

        # -------------------------------------------------------------
        # TEST 4: DPDP Act 2023 Parental Consent Engine
        # -------------------------------------------------------------
        from app.schemas.parental_consent import ParentalConsentCreate

        consent_req = ParentalConsentCreate(
            child_id=child.id,
            consent_type="SAFETY_MONITORING",
            verification_method="BIOMETRIC_AUTH",
            statutory_notice_accepted=True
        )

        consent_record = await consent_service.record_parental_consent(
            db=db,
            parent_user_id=mod_user.id,
            data=consent_req,
            ip_address="192.168.1.100"
        )
        assert consent_record.consent_status == "ACTIVE"

        verified = await consent_service.check_child_has_valid_consent(db, child.id)
        assert verified.has_valid_consent is True
        print("  [OK] DPDP Act 2023 verifiable parental consent flow verified")

        # -------------------------------------------------------------
        # TEST 5: Tightly Grounded Retrieval-Only RAG
        # -------------------------------------------------------------
        query = ModeratorGuidanceQuery(
            incident_type="grooming",
            observed_behavior="Adult asking child to move to WhatsApp and send photos",
            query_text="adult requesting private contact and explicit pictures from minor"
        )
        rag_res = StatutoryRAGCopilot.generate_grounded_guidance(query)
        assert rag_res.statutory_grounded is True
        assert rag_res.mandatory_reporting_required is True
        assert len(rag_res.statutory_citations) > 0
        assert any("POCSO" in c.statute_name for c in rag_res.statutory_citations)
        print("  [OK] Grounded retrieval-only RAG with mandatory citations verified")

    await engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    print("\nAll Architecture Guardrail Tests Passed Successfully! [100%]")

if __name__ == "__main__":
    asyncio.run(run_all_guardrail_tests())
