import asyncio
import os
import sys
import uuid
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.child import Child, Adult, AdultChildLink
from app.models.moderator import Moderator, Assignment
from app.models.case import Case, Incident, ModeratorNote, Report
from app.models.sos import SOSEvent
from app.models.notification import Notification, ChatMessage
from app.models.parental_consent import ParentalConsent
from app.models.evidence import Evidence
from app.models.audit import AuditLog
from app.models.missing_child import MissingChild, CCTVCandidate

from app.schemas.missing_child import MissingChildCreate, SightingCreate
from app.schemas.dpdp import ErasureRequestCreate

from app.services import missing_child_service, intelligence_service, dpdp_service
from app.core.security import get_password_hash

TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_phase9.db")
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
    ChatMessage.__table__,
    ParentalConsent.__table__,
    Evidence.__table__,
    AuditLog.__table__,
    MissingChild.__table__,
    CCTVCandidate.__table__,
    ModeratorNote.__table__,
    Report.__table__,
]

async def init_test_db():
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    async with test_engine.begin() as conn:
        for tbl in TEST_TABLES:
            await conn.run_sync(tbl.create, checkfirst=True)

async def test_missing_child_pipeline():
    print("Testing Missing Child Report, Sighting & Resolution Pipeline...")
    async with test_sessionmaker() as db:
        # 1. Create a reporter (parent) and moderator
        reporter = User(
            email="parent.verma@safety.in",
            hashed_password=get_password_hash("Password123"),
            full_name="Rajesh Verma",
            role="adult",
            state="Delhi",
            district="Delhi"
        )
        mod_user = User(
            email="officer.sharma@gov.in",
            hashed_password=get_password_hash("Password123"),
            full_name="Inspector Sharma",
            role="moderator",
            state="Delhi",
            district="Delhi"
        )
        db.add_all([reporter, mod_user])
        await db.commit()
        await db.refresh(reporter)
        await db.refresh(mod_user)

        mod = Moderator(user_id=mod_user.id, jurisdiction_state="Delhi", jurisdiction_district="Delhi", is_available=True)
        db.add(mod)
        await db.commit()
        await db.refresh(mod)

        # 2. File a missing child report
        create_req = MissingChildCreate(
            child_name="Aman Verma",
            photo_url="https://evidence.storage/missing/aman.jpg",
            description="10-year old boy missing from Lodhi Colony park since 4 PM.",
            age_when_missing=10,
            gender="Male",
            height_cm=135.0,
            weight_kg=32.0,
            clothing_description="Blue school uniform and red backpack",
            identifying_marks="Small scar on right elbow",
            last_known_address="Lodhi Garden, New Delhi",
            latitude=28.5933,
            longitude=77.2197,
            state="Delhi",
            district="Delhi"
        )
        mc_out = await missing_child_service.report_missing_child(db, create_req, reporter)
        assert mc_out.child_name == "Aman Verma"
        assert mc_out.status == "ACTIVE"

        # Verify critical case was generated
        case_res = await db.execute(select(Case).where(Case.id == mc_out.case_id))
        case = case_res.scalar_one_or_none()
        assert case is not None
        assert case.priority == "critical"
        assert "Aman Verma" in case.title

        # 3. List active alerts
        alerts = await missing_child_service.list_active_missing_children(db)
        assert len(alerts) >= 1
        assert alerts[0].child_name == "Aman Verma"

        # 4. Submit citizen sighting
        sighting_req = SightingCreate(
            image_url="https://evidence.storage/sightings/sighting_metro.jpg",
            location_address="Near Central Secretariat Metro Station",
            latitude=28.6150,
            longitude=77.2120,
            sighting_notes="Spotted a boy matching the description asking for directions."
        )
        sighting_out = await missing_child_service.submit_sighting(db, mc_out.id, sighting_req, reporter)
        assert sighting_out.missing_child_id == mc_out.id
        assert sighting_out.status == "PENDING_REVIEW"

        # 5. Moderator verifies sighting
        verified_sighting = await missing_child_service.verify_sighting(
            db, sighting_out.id, mod_user, is_match=True, notes="CCTV footage at gate 2 confirms match."
        )
        assert verified_sighting.status == "VERIFIED_MATCH"
        assert verified_sighting.verified_by == mod_user.id

        # 6. Resolve missing child case (Found)
        resolved_mc = await missing_child_service.resolve_missing_child(
            db, mc_out.id, mod_user, "Child safely secured by PCR van and reunited with family."
        )
        assert resolved_mc.status == "FOUND"

        # Verify linked case was closed
        await db.refresh(case)
        assert case.status == "closed"
        print("  Missing Child reporting, sighting submission, verification, and resolution -> PASS")

async def test_longitudinal_intelligence():
    print("Testing Longitudinal Intelligence (Timeline, Cross-Case Patterns, Dossier)...")
    async with test_sessionmaker() as db:
        # Create a child with historical infractions
        child = Child(
            protected_child_id="C-MH-MUM-77777",
            display_name="Maya Sen",
            age=14,
            state="Maharashtra",
            district="Mumbai",
            is_active=True
        )
        db.add(child)
        await db.commit()
        await db.refresh(child)

        # Create 2 cases
        case1 = Case(child_id=child.id, protected_case_id="CASE-11111111", title="Cyber Incident 1", status="closed", priority="medium")
        case2 = Case(child_id=child.id, protected_case_id="CASE-22222222", title="Active Threats", status="investigating", priority="high")
        db.add_all([case1, case2])
        await db.commit()
        await db.refresh(case1)
        await db.refresh(case2)

        # Create recurring grooming incidents across cases
        inc1 = Incident(case_id=case1.id, incident_type="grooming_attempt", severity="medium", description="Stranger asked for private discord", trust_level="unverified", source="ai_monitor")
        inc2 = Incident(case_id=case2.id, incident_type="grooming_explicit", severity="critical", description="Blackmail threat with altered photos", trust_level="unverified", source="ai_monitor")
        # Add 2 SOS beacons
        sos1 = SOSEvent(child_id=child.id, case_id=case1.id, latitude=19.0760, longitude=72.8777, status="resolved")
        sos2 = SOSEvent(child_id=child.id, case_id=case2.id, latitude=19.0780, longitude=72.8790, status="active", is_silent_duress=True)
        db.add_all([inc1, inc2, sos1, sos2])
        await db.commit()

        # 1. Test Safety Timeline
        timeline = await intelligence_service.get_child_safety_timeline(db, child.id)
        assert timeline.child_id == child.id
        assert timeline.total_events >= 4
        # Verify chronological order
        timestamps = [e.timestamp for e in timeline.events]
        assert timestamps == sorted(timestamps)

        # 2. Test Cross-Case Pattern Detector
        patterns = await intelligence_service.detect_cross_case_patterns(db, child.id)
        assert patterns.total_patterns_detected >= 2
        pattern_types = [p.pattern_type for p in patterns.patterns]
        assert "RECURRING_GROOMING_THREAT" in pattern_types
        assert "FREQUENT_EMERGENCY_DURESS" in pattern_types
        assert patterns.highest_risk_level == "CRITICAL"

        # 3. Test Moderator Dossier Report
        report = await intelligence_service.generate_moderator_intelligence_report(db, child.id)
        assert report.total_cases == 2
        assert report.total_sos_events == 2
        assert report.risk_trajectory == "ESCALATING_CRITICAL"
        assert len(report.statutory_triggers) >= 2
        assert "POCSO" in report.statutory_triggers[0]
        print("  Longitudinal Timeline, Pattern Detector, and Moderator Dossier -> PASS")

async def test_dpdp_compliance_and_age_of_majority():
    print("Testing DPDP Act 2023 Compliance & 18+ Age of Majority Transition...")
    async with test_sessionmaker() as db:
        # 1. Create a child who just turned 18 (DOB = 18 years ago today)
        dob_18 = date.today() - timedelta(days=365 * 18 + 5)
        user_18 = User(
            email="aarav.turning18@safety.in",
            hashed_password=get_password_hash("Password123"),
            full_name="Aarav Joshi",
            role="child",
            state="Karnataka",
            district="Bangalore"
        )
        db.add(user_18)
        await db.commit()
        await db.refresh(user_18)

        child_18 = Child(
            user_id=user_18.id,
            protected_child_id="C-KA-BLR-18181",
            display_name="Aarav Joshi",
            date_of_birth=dob_18,
            state="Karnataka",
            district="Bangalore"
        )
        db.add(child_18)
        await db.commit()
        await db.refresh(child_18)

        # Parent Guardian
        parent = User(email="parent.joshi@safety.in", hashed_password=get_password_hash("P@ss1234"), role="adult")
        db.add(parent)
        await db.commit()
        await db.refresh(parent)
        
        adult_rec = Adult(user_id=parent.id)
        db.add(adult_rec)
        await db.commit()
        await db.refresh(adult_rec)

        link = AdultChildLink(adult_id=adult_rec.id, child_id=child_18.id, relationship="Father", is_primary=True, linked_at=datetime.utcnow())
        consent = ParentalConsent(parent_user_id=parent.id, child_id=child_18.id, consent_status="ACTIVE")
        db.add_all([link, consent])
        await db.commit()

        # 2. Run Age-of-Majority Sweep
        sweep_res = await dpdp_service.check_age_of_majority_transitions(db)
        assert sweep_res.transitions_executed >= 1
        assert str(child_18.id) in sweep_res.transitioned_child_ids

        # Verify User was promoted to adult
        await db.refresh(user_18)
        assert user_18.role == "adult", "User must be promoted to adult self-custody upon reaching age of majority"

        # Verify ParentalConsent was expired
        await db.refresh(consent)
        assert consent.consent_status == "EXPIRED_AGE_OF_MAJORITY"

        # Verify Guardian link was severed
        links_res = await db.execute(select(AdultChildLink).where(AdultChildLink.child_id == child_18.id))
        assert len(links_res.scalars().all()) == 0, "All guardian surveillance links must be severed at age 18"

        # 3. Test DPDP Rights and Erasure Request
        rights = await dpdp_service.get_user_dpdp_rights(db, user_18)
        assert rights.is_adult_self_custody == True
        assert rights.eligible_for_erasure == True

        erasure_req = ErasureRequestCreate(reason="Account closed, requesting personal data erasure.")
        erasure_out = await dpdp_service.submit_erasure_request(db, user_18, erasure_req)
        assert erasure_out.status == "PENDING_STATUTORY_REVIEW"

        # 4. Test Dual-Track Retention Sweep
        # Create an old read notification
        old_notif = Notification(
            user_id=user_18.id,
            notification_type="SYSTEM",
            title="Old Notice",
            body="Old notice from 100 days ago",
            is_read=True
        )
        old_notif.created_at = datetime.utcnow() - timedelta(days=100)
        db.add(old_notif)
        await db.commit()

        retention_res = await dpdp_service.run_dual_track_data_retention_sweep(db)
        assert retention_res.operational_logs_purged >= 1

        print("  Age-of-majority transition, consent expiration, guardian link severing, DPDP rights & retention sweep -> PASS")

async def main():
    print("=" * 60)
    print("RUNNING PHASE 9 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    await init_test_db()
    await test_missing_child_pipeline()
    await test_longitudinal_intelligence()
    await test_dpdp_compliance_and_age_of_majority()
    print("=" * 60)
    print("ALL PHASE 9 BACKEND TESTS PASSED! 100% SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
