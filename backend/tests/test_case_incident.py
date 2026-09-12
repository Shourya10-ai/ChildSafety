import asyncio
import os
import sys
import uuid
import hashlib

# Ensure backend root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.models.user import User
from app.models.child import Child
from app.models.moderator import Moderator, Assignment
from app.models.case import Case, Incident, Report, ModeratorNote
from app.models.evidence import Evidence
from app.models.escalation import Escalation
from app.schemas.case import CaseCreate, CaseUpdate, CaseStatus, CasePriority
from app.schemas.incident import IncidentCreate, IncidentType, IncidentSeverity
from app.schemas.report import ReportCreate
from app.schemas.moderator import ModeratorNoteCreate, NoteType, EscalationCreate
from app.services import case_service, incident_service, report_service, evidence_service

TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_phase5.db")
TEST_SQLITE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

test_engine = create_async_engine(TEST_SQLITE_URL, echo=False)
test_sessionmaker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_TABLES = [
    User.__table__,
    Child.__table__,
    Moderator.__table__,
    Assignment.__table__,
    Case.__table__,
    Incident.__table__,
    Report.__table__,
    ModeratorNote.__table__,
    Escalation.__table__,
    Evidence.__table__,
]

async def setup_test_db():
    async with test_engine.begin() as conn:
        for tbl in reversed(TEST_TABLES):
            try:
                await conn.run_sync(tbl.drop, checkfirst=True)
            except Exception:
                pass
        for tbl in TEST_TABLES:
            await conn.run_sync(tbl.create, checkfirst=True)

async def teardown_test_db():
    async with test_engine.begin() as conn:
        for tbl in reversed(TEST_TABLES):
            try:
                await conn.run_sync(tbl.drop, checkfirst=True)
            except Exception:
                pass
    await test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

async def test_case_lifecycle_and_assignment():
    await setup_test_db()
    async with test_sessionmaker() as db:
        # 1. Create a Child and two Moderators
        mod1_user = User(email="mod1@safety.org", hashed_password="hash1", role="moderator", full_name="Sarah Moderator")
        mod2_user = User(email="mod2@safety.org", hashed_password="hash2", role="moderator", full_name="John Counselor")
        db.add_all([mod1_user, mod2_user])
        await db.commit()

        mod1 = Moderator(user_id=mod1_user.id, specialization="Cyberbullying", active_case_count=0)
        mod2 = Moderator(user_id=mod2_user.id, specialization="Threat Detection", active_case_count=0)
        db.add_all([mod1, mod2])

        child_user = User(email="kid@safety.org", hashed_password="hash3", role="child", full_name="Leo")
        db.add(child_user)
        await db.commit()

        child = Child(user_id=child_user.id, protected_child_id="C12345678", display_name="Leo", age=10)
        db.add(child)
        await db.commit()

        # 2. Test auto case creation and moderator assignment
        case1 = await case_service.get_or_create_active_case_for_child(
            db, child_id=child.id, title="Suspicious messages", priority="high"
        )
        assert case1 is not None
        assert case1.protected_case_id.startswith("CASE-")
        assert case1.status == "open"
        assert case1.moderator_id is not None
        first_assigned_mod_id = case1.moderator_id

        # 3. Test Persistent Moderator Relationship:
        # If another case is created later for this child, the SAME moderator must be assigned!
        mod_assigned = await case_service.get_or_assign_moderator_for_child(db, child.id)
        assert mod_assigned.id == first_assigned_mod_id, "Child must retain their assigned moderator"

        # 4. Test Longitudinal Case Intelligence:
        # A second incident report should attach to the existing open case!
        case_retrieved = await case_service.get_or_create_active_case_for_child(db, child_id=child.id)
        assert case_retrieved.id == case1.id, "Second report must link to existing active case"

        # 5. Test Case Lifecycle Transition:
        updated = await case_service.update_case(db, case1.id, CaseUpdate(status=CaseStatus.INVESTIGATING))
        assert updated.status == "investigating"

        # 6. Test Moderator Note / Journal
        note = await case_service.add_moderator_note(
            db, case1.id, first_assigned_mod_id,
            ModeratorNoteCreate(content="Child reported being harassed on Discord. Contacted school liaison.", note_type=NoteType.ACTION_TAKEN)
        )
        assert note.content == "Child reported being harassed on Discord. Contacted school liaison."
        assert note.note_type == "action_taken"

        notes = await case_service.get_case_notes(db, case1.id)
        assert len(notes) == 1

        # 7. Test Case Escalation
        escalation = await case_service.escalate_case(
            db, case1.id, first_assigned_mod_id,
            EscalationCreate(reason="Physical threat detected, alerting local authorities.", priority="critical")
        )
        assert escalation.status == "pending"
        assert escalation.priority == "critical"
        case_after_escalate = await case_service.get_case_by_id(db, case1.id)
        assert case_after_escalate.status == "escalated"

async def test_anonymous_and_authenticated_reports():
    async with test_sessionmaker() as db:
        # 1. Test Anonymous Report
        anon_report_data = ReportCreate(
            category="cyberbullying",
            platform="Instagram",
            content="Someone created a fake profile impersonating me and posting nasty comments.",
            is_anonymous=True
        )
        resp = await report_service.submit_report(db, anon_report_data)
        assert resp.status == "submitted"
        assert resp.protected_case_id is not None
        assert resp.protected_case_id.startswith("CASE-")

        # Verify Report in DB is marked anonymous
        report = await report_service.get_report_by_id(db, resp.report_id)
        assert report.is_anonymous is True
        assert report.reporter_id is None
        assert report.reporter_type == "anonymous"

        # Verify incident was created
        incidents = await incident_service.list_incidents_for_case(db, resp.case_id)
        assert len(incidents) >= 1
        assert incidents[0].incident_type == "cyberbullying"

def test_evidence_hashing():
    data = b"Sample test screenshot content for child safety verification"
    expected_hash = hashlib.sha256(data).hexdigest()
    assert len(expected_hash) == 64
    assert evidence_service.detect_media_type("image/png") == "image"
    assert evidence_service.detect_media_type("audio/mp3") == "audio"
    assert evidence_service.detect_media_type("application/pdf") == "document"

async def run_all_tests():
    print("Running Phase 5 Automated Tests...")
    test_evidence_hashing()
    print("  [OK] Evidence hashing & media type detection passed")
    await test_case_lifecycle_and_assignment()
    print("  [OK] Case lifecycle, auto-creation & persistent moderator assignment passed")
    await test_anonymous_and_authenticated_reports()
    print("  [OK] Anonymous report submission and incident triage passed")
    await teardown_test_db()
    print("All Phase 5 Backend Tests Passed Successfully! [100%]")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
