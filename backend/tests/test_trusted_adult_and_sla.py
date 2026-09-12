import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.child import Child, Adult, AdultChildLink
from app.models.moderator import Moderator, Assignment
from app.models.case import Case, Incident, ModeratorNote
from app.models.sos import SOSEvent
from app.models.notification import Notification
from app.schemas.sos import SOSTriggerRequest
from app.services import child_service, sos_service, sla_service

TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_phase7.db")
TEST_SQLITE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

test_engine = create_async_engine(TEST_SQLITE_URL, echo=False)
test_sessionmaker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_TABLES = [
    User.__table__,
    Child.__table__,
    Adult.__table__,
    AdultChildLink.__table__,
    Moderator.__table__,
    Assignment.__table__,
    Case.__table__,
    Incident.__table__,
    SOSEvent.__table__,
    Notification.__table__,
    ModeratorNote.__table__,
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

async def run_all_tests():
    await setup_test_db()
    try:
        async with test_sessionmaker() as db:
            print("--- Starting Phase 7 Backend Tests ---")
            
            # Seed users
            child_user = User(
                email="child_victim@test.local",
                hashed_password="pw",
                role="child",
                full_name="Aarav Sharma"
            )
            abusive_guardian_user = User(
                email="guardian_home@test.local",
                hashed_password="pw",
                role="adult",
                full_name="Household Guardian",
                phone="+919800000001"
            )
            trusted_aunt_user = User(
                email="aunt_priya@test.local",
                hashed_password="pw",
                role="adult",
                full_name="Priya Sharma (Aunt)",
                phone="+919800000002"
            )
            mod_user = User(
                email="moderator1@safety.gov.in",
                hashed_password="pw",
                role="moderator",
                full_name="Duty Officer Rajesh"
            )
            supervisor_user = User(
                email="supervisor@safety.gov.in",
                hashed_password="pw",
                role="moderator",
                full_name="Supervisor Ananya"
            )
            db.add_all([child_user, abusive_guardian_user, trusted_aunt_user, mod_user, supervisor_user])
            await db.commit()
            for u in [child_user, abusive_guardian_user, trusted_aunt_user, mod_user, supervisor_user]:
                await db.refresh(u)

            # Create Child
            child = Child(
                user_id=child_user.id,
                protected_child_id="CHD-TEST-701",
                display_name="Aarav",
                age=12
            )
            db.add(child)

            # Create Primary Guardian Adult & Link
            guardian_adult = Adult(
                user_id=abusive_guardian_user.id,
                phone=abusive_guardian_user.phone
            )
            db.add(guardian_adult)

            # Create Moderators: mod has 0 cases (so gets assigned first), supervisor has 2 cases
            mod = Moderator(user_id=mod_user.id, is_available=True, active_case_count=0, max_cases=10)
            sup = Moderator(user_id=supervisor_user.id, is_available=True, active_case_count=2, max_cases=10)
            db.add_all([mod, sup])
            await db.commit()
            await db.refresh(child)
            await db.refresh(guardian_adult)
            await db.refresh(mod)
            await db.refresh(sup)

            # Primary Guardian link
            primary_link = AdultChildLink(
                adult_id=guardian_adult.id,
                child_id=child.id,
                relationship="parent",
                is_primary=True,
                is_verified=True,
                linked_at=datetime.utcnow()
            )
            db.add(primary_link)
            await db.commit()

            # Test 1: Trusted-Adult Nomination
            print("Running Test 1: Child nominates alternate trusted adult...")
            nom_link = await child_service.nominate_trusted_adult(
                db=db,
                child_id=child.id,
                adult_identifier="aunt_priya@test.local",
                relationship_label="Maternal Aunt Priya",
                reason="Protective adult outside abusive home"
            )
            assert nom_link.is_alternate_trusted_adult is True
            assert nom_link.nomination_status == "PENDING_VETTING"
            assert nom_link.relationship_label == "Maternal Aunt Priya"
            print("  [PASS] Nomination created with PENDING_VETTING status.")

            # Test 2: Moderator Reviews & Approves Nomination
            print("Running Test 2: Safety moderator reviews & approves nomination...")
            vetted_link = await child_service.review_trusted_adult_nomination(
                db=db,
                link_id=nom_link.id,
                moderator_id=mod.id,
                approved=True,
                vetting_notes="Identity and relationship verified via emergency helpline interview."
            )
            assert vetted_link.nomination_status == "APPROVED"
            assert vetted_link.is_verified is True
            assert vetted_link.vetted_by_moderator_id == mod.id

            # Verify list of trusted adults for child
            trusted_list = await child_service.get_trusted_adults_for_child(db, child.id)
            assert len(trusted_list) == 2
            assert any(t["relationship_label"] == "Maternal Aunt Priya" for t in trusted_list)
            print("  [PASS] Trusted adult vetted and approved.")

            # Test 3: Silent/Duress SOS Bypasses Primary Household Guardian
            print("Running Test 3: Duress SOS triggers and routes exclusively to alternate trusted adult...")
            sos_req = SOSTriggerRequest(
                child_id=child.id,
                latitude=28.6139,
                longitude=77.2090,
                location_address="Connaught Place, New Delhi",
                is_silent_duress=True,
                bypass_primary_guardians=True,
                message="Household violence in progress, need quiet rescue"
            )
            sos_res = await sos_service.trigger_sos(db, sos_req, user_id=child_user.id)
            assert sos_res.is_silent_duress is True
            assert sos_res.routed_to_alternate_adults_only is True

            # Query generated notifications
            notifs_res = await db.execute(select(Notification))
            notifs = notifs_res.scalars().all()

            notified_user_ids = {n.user_id for n in notifs}
            # Crucial verification: Abusive primary guardian must NOT have received any notification!
            assert abusive_guardian_user.id not in notified_user_ids, "CRITICAL SECURITY BREACH: Abusive household guardian received notification during duress SOS!"
            # Approved alternate trusted adult MUST have received notification
            assert trusted_aunt_user.id in notified_user_ids, "Alternate trusted adult was not notified!"
            print(f"  [PASS] Duress alert successfully shielded from abusive guardian and delivered to trusted aunt.")

            # Test 4: SLA Auto-Escalation & Workload Reassignment
            print("Running Test 4: SLA Auto-Escalation & delinquent case reassignment...")
            # Retrieve the case created for the SOS
            case_res = await db.execute(select(Case).where(Case.id == sos_res.case_id))
            case = case_res.scalar_one()

            # Ensure SLA initialized
            await sla_service.apply_sla_to_case(db, case)
            assert case.sla_tier == "EMERGENCY_SOS_15MIN"
            assert case.sla_deadline is not None
            assert case.sla_breached is False

            # Artificially age the deadline by 30 minutes in the past
            case.sla_deadline = datetime.utcnow() - timedelta(minutes=30)
            await db.commit()

            # Trigger SLA enforcement
            enforce_result = await sla_service.check_and_enforce_case_slas(db)
            assert enforce_result["total_breached_detected"] == 1
            assert enforce_result["total_reassigned"] == 1

            # Refresh case to verify updates
            await db.refresh(case)
            assert case.sla_breached is True
            assert case.escalation_level == 1
            assert case.moderator_id == sup.id, "Case was not reassigned to available supervisor!"

            # Check that an SLA escalation note was logged
            notes_res = await db.execute(select(ModeratorNote).where(ModeratorNote.case_id == case.id))
            notes = notes_res.scalars().all()
            assert any("SLA ENFORCER" in n.content for n in notes)
            print("  [PASS] Overdue SOS case successfully auto-escalated to supervisor Ananya with audit log.")

            print("=== ALL PHASE 7 BACKEND TESTS PASSED ===")
    finally:
        await teardown_test_db()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
