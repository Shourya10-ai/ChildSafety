import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.user import User
from app.models.child import Child, Adult, AdultChildLink
from app.models.moderator import Moderator, Assignment
from app.models.case import Case, Incident
from app.models.sos import SOSEvent
from app.models.notification import Notification
from app.schemas.sos import SOSTriggerRequest, SOSResolveRequest
from app.services import sos_service, notification_service

TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_phase6.db")
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

async def test_sos_workflow_and_notification_chain():
    await setup_test_db()
    async with test_sessionmaker() as db:
        # 1. Setup Child, Parent Adult, and Linked Relationship
        parent_user = User(email="parent@safety.org", hashed_password="pwd", role="adult", full_name="Priya Sharma")
        child_user = User(email="aarav@safety.org", hashed_password="pwd", role="child", full_name="Aarav Sharma")
        db.add_all([parent_user, child_user])
        await db.commit()

        adult = Adult(user_id=parent_user.id, phone="9876543210")
        child = Child(user_id=child_user.id, protected_child_id="CAARAV123", display_name="Aarav", age=11)
        db.add_all([adult, child])
        await db.commit()

        from datetime import datetime, timezone
        link = AdultChildLink(adult_id=adult.id, child_id=child.id, relationship="Mother", linked_at=datetime.now(timezone.utc))
        db.add(link)
        await db.commit()

        # 2. Trigger SOS
        trigger_req = SOSTriggerRequest(
            child_id=child.id,
            latitude=28.6139,
            longitude=77.2090,
            accuracy=12.5,
            location_address="Connaught Place, New Delhi",
            message="Need help immediately!"
        )
        sos_event = await sos_service.trigger_sos(db, trigger_req, user_id=child_user.id)

        assert sos_event is not None
        assert sos_event.status == "active"
        assert sos_event.latitude == 28.6139
        assert sos_event.longitude == 77.2090
        assert sos_event.child_name == "Aarav"
        assert sos_event.notified_guardians_count == 1
        assert sos_event.protected_case_id is not None
        assert sos_event.protected_case_id.startswith("CASE-")

        # 3. Verify Notification Chain: Parent received urgent notification
        notifs = await notification_service.get_user_notifications(db, parent_user.id)
        assert notifs.unread_count >= 1
        sos_notif = notifs.items[0]
        assert "EMERGENCY" in sos_notif.title
        assert "Aarav" in sos_notif.body
        assert sos_notif.notification_type == "sos_alert"
        assert sos_notif.data.get("latitude") == 28.6139

        # 4. Verify Active SOS Query
        active_list = await sos_service.get_active_sos_events(db)
        assert len(active_list) == 1
        assert active_list[0].id == sos_event.id

        # 5. Verify Haversine Proximity Query
        # Within 5km (target is exact point): should find it
        nearby = await sos_service.get_nearby_sos_events(db, latitude=28.6140, longitude=77.2091, radius_km=5.0)
        assert len(nearby) == 1
        # Outside 1km (from 50km away, e.g. Gurgaon 28.4595, 77.0266): should not find it within 5km radius
        far_away = await sos_service.get_nearby_sos_events(db, latitude=28.4595, longitude=77.0266, radius_km=5.0)
        assert len(far_away) == 0

        # 6. Verify Resolution Workflow
        resolved_event = await sos_service.resolve_sos(db, sos_event.id, resolver_user_id=parent_user.id, message="Child found safe with teacher.")
        assert resolved_event.status == "resolved"
        assert resolved_event.resolved_at is not None
        assert "Child found safe with teacher" in (resolved_event.message or "")

        # Verify no active events left
        remaining_active = await sos_service.get_active_sos_events(db)
        assert len(remaining_active) == 0

async def run_all_tests():
    print("Running Phase 6 SOS & Emergency Automated Tests...")
    await test_sos_workflow_and_notification_chain()
    print("  [OK] SOS trigger, GPS capture, auto critical case passed")
    print("  [OK] Emergency notification chain to linked adults passed")
    print("  [OK] Haversine proximity query passed")
    print("  [OK] Emergency resolution workflow passed")
    await teardown_test_db()
    print("All Phase 6 SOS & Emergency Tests Passed Successfully! [100%]")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
