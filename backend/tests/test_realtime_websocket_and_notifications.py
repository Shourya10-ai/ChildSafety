import asyncio
import os
import sys
import uuid
from datetime import datetime

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
from app.schemas.case import CaseStatus
from app.services import sos_service, case_service, notification_service
from app.core.websocket_manager import ws_manager

TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_phase8.db")
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

class MockWebSocket:
    def __init__(self):
        self.received_messages = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, text: str):
        self.received_messages.append(text)

async def run_phase8_tests():
    await setup_test_db()
    try:
        async with test_sessionmaker() as db:
            print("--- Starting Phase 8 Real-Time WebSocket & Notification Tests ---")

            # Seed child, moderator, adult
            child_user = User(email="child_ws@test.local", hashed_password="pw", role="child", full_name="Tanvi")
            mod_user = User(email="mod_ws@test.local", hashed_password="pw", role="moderator", full_name="Officer Raman")
            db.add_all([child_user, mod_user])
            await db.commit()
            await db.refresh(child_user)
            await db.refresh(mod_user)

            child = Child(user_id=child_user.id, protected_child_id="CHD-WS-801", display_name="Tanvi", age=13)
            mod = Moderator(user_id=mod_user.id, is_available=True, active_case_count=0, max_cases=15)
            db.add_all([child, mod])
            await db.commit()
            await db.refresh(child)
            await db.refresh(mod)

            # Test 1: Connect Mock WebSocket to ws_manager
            print("Running Test 1: Connect WebSocket client to manager...")
            mock_ws = MockWebSocket()
            await ws_manager.connect(mock_ws, user_id=str(mod_user.id), role="moderator")
            assert mock_ws.accepted is True
            assert mock_ws in ws_manager.role_connections["moderator"]
            print("  [PASS] WebSocket client connected and registered to role 'moderator'.")

            # Test 2: Trigger SOS and verify real-time event dispatch
            print("Running Test 2: Trigger SOS and verify real-time WebSocket broadcast...")
            sos_req = SOSTriggerRequest(
                child_id=child.id,
                latitude=19.0760,
                longitude=72.8777,
                location_address="Mumbai Central",
                message="Help needed"
            )
            sos_res = await sos_service.trigger_sos(db, sos_req, user_id=child_user.id)
            assert sos_res.id is not None

            # Verify mock_ws received SOS_TRIGGERED event
            assert len(mock_ws.received_messages) > 0
            latest_msg = mock_ws.received_messages[-1]
            assert "SOS_TRIGGERED" in latest_msg
            assert "Mumbai Central" in latest_msg
            print("  [PASS] Real-time SOS_TRIGGERED event dispatched to connected WebSocket clients.")

            # Test 3: Resolve SOS and verify resolution event
            print("Running Test 3: Resolve SOS and verify SOS_RESOLVED event...")
            resolve_res = await sos_service.resolve_sos(db, sos_id=sos_res.id, resolver_user_id=mod_user.id, message="Child escorted safely")
            assert resolve_res.status == "resolved"

            latest_msg = mock_ws.received_messages[-1]
            assert "SOS_RESOLVED" in latest_msg
            assert "resolved" in latest_msg
            print("  [PASS] Real-time SOS_RESOLVED event dispatched successfully.")

            # Test 4: Case status change event
            print("Running Test 4: Case status transition event broadcast...")
            trans_res = await case_service.transition_case_status(
                db=db,
                case_id=sos_res.case_id,
                to_status=CaseStatus.INVESTIGATING,
                reason="Officer dispatched to location",
                actor_id=mod.id,
                actor_role="moderator"
            )
            assert trans_res.status == "investigating"

            assert any("CASE_STATUS_CHANGED" in m for m in mock_ws.received_messages)
            print("  [PASS] Real-time CASE_STATUS_CHANGED event broadcast verified.")

            # Test 5: Notification Management Endpoints
            print("Running Test 5: Notification management (read single and read all)...")
            n1 = Notification(user_id=mod_user.id, notification_type="test", title="Alert 1", body="Body 1", is_read=False)
            n2 = Notification(user_id=mod_user.id, notification_type="test", title="Alert 2", body="Body 2", is_read=False)
            db.add_all([n1, n2])
            await db.commit()

            notifs = await notification_service.get_user_notifications(db, mod_user.id)
            assert notifs.unread_count >= 2

            # Mark single read
            ok = await notification_service.mark_notification_read(db, n1.id, mod_user.id)
            assert ok is True

            # Mark all read
            cleared = await notification_service.mark_all_notifications_read(db, mod_user.id)
            assert cleared >= 1

            notifs_after = await notification_service.get_user_notifications(db, mod_user.id)
            assert notifs_after.unread_count == 0
            print("  [PASS] Notification unread count and read-all workflows verified.")

            # Disconnect
            ws_manager.disconnect(mock_ws, user_id=str(mod_user.id), role="moderator")
            print("=== ALL PHASE 8 BACKEND REAL-TIME TESTS PASSED ===")
    finally:
        await teardown_test_db()

if __name__ == "__main__":
    asyncio.run(run_phase8_tests())
