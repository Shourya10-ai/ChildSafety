import asyncio
import os
import sys
import uuid
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.child import Child, Adult, AdultChildLink
from app.models.moderator import Moderator, Assignment
from app.models.case import Case, Incident, ModeratorNote
from app.models.notification import ChatMessage, Notification
from app.schemas.auth import RegisterRequest, UserRole, LoginRequest, ClaimChildAccountRequest
from app.schemas.chat import ChatMessageCreate
from app.services.auth_service import AuthService
from app.services import chat_service
from app.core.security import generate_protected_child_id
from app.utils.india_locations import get_location_codes

import fakeredis.aioredis as fake_redis

TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_foundation_hardening.db")
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
    Notification.__table__,
    ChatMessage.__table__,
    ModeratorNote.__table__,
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

async def test_location_encoded_ids():
    print("Testing Location-Encoded Protected Child ID...")
    st_code, dst_code = get_location_codes("Maharashtra", "Mumbai")
    assert st_code == "MH"
    assert dst_code == "MUM"

    st_code_dl, dst_code_dl = get_location_codes("Delhi", "New Delhi")
    assert st_code_dl == "DL"
    assert dst_code_dl == "NDL"

    pid = generate_protected_child_id("Maharashtra", "Mumbai")
    assert pid.startswith("C-MH-MUM-")
    assert len(pid) == len("C-MH-MUM-") + 5

    pid_dl = generate_protected_child_id("Delhi", "South Delhi")
    assert pid_dl.startswith("C-DL-SDL-")
    print(f"  Generated IDs: {pid}, {pid_dl} -> PASS")

async def test_solo_domestic_danger_registration():
    print("Testing Solo / Domestic Danger Child Registration...")
    redis_client = fake_redis.FakeRedis()
    async with test_sessionmaker() as db:
        auth_service = AuthService(db, redis_client)

        # 1. Pre-register a guardian adult
        adult_data = RegisterRequest(
            email="parent@safety.in",
            password="Password123",
            full_name="Parent Sharma",
            role=UserRole.ADULT,
            phone="9876543210",
            state="Maharashtra",
            district="Mumbai",
            pin_code="400001"
        )
        adult_tok = await auth_service.register(adult_data)
        assert adult_tok.role == "adult"

        # 2. Solo child tries to use adult's email -> MUST BE REJECTED
        from fastapi import HTTPException
        solo_invalid = RegisterRequest(
            email="parent@safety.in",
            password="Password123",
            full_name="Rohan Sharma",
            role=UserRole.CHILD,
            setup_path="SOLO",
            state="Maharashtra",
            district="Mumbai"
        )
        rejected = False
        try:
            await auth_service.register(solo_invalid)
        except HTTPException as e:
            rejected = True
            assert "Email already registered" in str(e.detail) or "safety" in str(e.detail)
        assert rejected, "Child should not be able to use an already registered parent email for solo setup"

        # 3. Solo child uses their own personal/school email
        solo_valid = RegisterRequest(
            email="rohan.school@student.org",
            password="Password123",
            full_name="Rohan Sharma",
            role=UserRole.CHILD,
            setup_path="SOLO",
            state="Maharashtra",
            district="Mumbai",
            pin_code="400001",
            school_name="Kendriya Vidyalaya Mumbai",
            date_of_birth=date(2012, 5, 15)
        )
        tok = await auth_service.register(solo_valid)
        assert tok.role == "child"
        assert tok.is_domestic_safety_mode == True
        assert tok.setup_path == "SOLO"
        assert tok.protected_child_id.startswith("C-MH-MUM-")

        # Verify child record in DB
        res = await db.execute(select(Child).where(Child.protected_child_id == tok.protected_child_id))
        child = res.scalar_one_or_none()
        assert child is not None
        assert child.is_domestic_safety_mode == True
        assert child.school_name == "Kendriya Vidyalaya Mumbai"

        # Verify NO adult link created
        links_res = await db.execute(select(AdultChildLink).where(AdultChildLink.child_id == child.id))
        assert len(links_res.all()) == 0, "Solo domestic danger child must have NO primary adult link"

        # Verify Case was auto-created
        cases_res = await db.execute(select(Case).where(Case.child_id == child.id))
        cases = cases_res.scalars().all()
        assert len(cases) == 1
        assert "Domestic Safety" in cases[0].title
        print(f"  Solo domestic registration created {tok.protected_child_id} with automatic case -> PASS")

async def test_collaborative_adult_linked_registration():
    print("Testing Collaborative Adult-Linked Child Registration...")
    redis_client = fake_redis.FakeRedis()
    async with test_sessionmaker() as db:
        auth_service = AuthService(db, redis_client)

        from app.core.security import get_password_hash
        adult_user = User(
            email="anita.guardian@gmail.com",
            hashed_password=get_password_hash("Password123"),
            full_name="Anita Roy",
            role="adult",
            phone="9811122233",
            state="Delhi",
            district="Delhi"
        )
        db.add(adult_user)
        await db.commit()
        await db.refresh(adult_user)

        # 2. Child registers with parent email shortcut
        child_req = RegisterRequest(
            email="priya.roy@gmail.com",
            password="Password123",
            full_name="Priya Roy",
            role=UserRole.CHILD,
            setup_path="COLLABORATIVE",
            linked_via_adult_email="anita.guardian@gmail.com",
            relationship_to_child="Mother",
            state="Delhi",
            district="Delhi",
            pin_code="110001",
            date_of_birth=date(2013, 8, 20)
        )
        tok = await auth_service.register(child_req)
        assert tok.role == "child"
        assert tok.is_domestic_safety_mode == False
        assert tok.protected_child_id.startswith("C-DL-DEL-")

        # Verify AdultChildLink was created automatically!
        c_res = await db.execute(select(Child).where(Child.protected_child_id == tok.protected_child_id))
        child = c_res.scalar_one_or_none()
        assert child is not None

        links_res = await db.execute(select(AdultChildLink).where(AdultChildLink.child_id == child.id))
        links = links_res.scalars().all()
        assert len(links) == 1
        assert links[0].relationship == "Mother"
        assert links[0].is_primary == True
        assert links[0].is_verified == True
        print(f"  Collaborative registration successfully linked child to adult -> PASS")

async def test_location_priority_moderator_assignment():
    print("Testing Location-Priority Moderator Assignment...")
    async with test_sessionmaker() as db:
        # Create a Mumbai moderator and a Delhi moderator
        from app.core.security import get_password_hash
        u_mum = User(email="mod.mumbai@gov.in", hashed_password=get_password_hash("P@ss1234"), role="moderator", full_name="Inspector Deshmukh")
        u_del = User(email="mod.delhi@gov.in", hashed_password=get_password_hash("P@ss1234"), role="moderator", full_name="Inspector Verma")
        db.add_all([u_mum, u_del])
        await db.commit()
        await db.refresh(u_mum)
        await db.refresh(u_del)

        mod_mum = Moderator(user_id=u_mum.id, jurisdiction_state="Maharashtra", jurisdiction_district="Mumbai", is_available=True)
        mod_del = Moderator(user_id=u_del.id, jurisdiction_state="Delhi", jurisdiction_district="Delhi", is_available=True)
        db.add_all([mod_mum, mod_del])
        await db.commit()
        await db.refresh(mod_mum)
        await db.refresh(mod_del)

        # Create a child in Mumbai
        child_mum = Child(
            protected_child_id="C-MH-MUM-99999",
            display_name="Aarav",
            state="Maharashtra",
            district="Mumbai",
            setup_path="SOLO"
        )
        db.add(child_mum)
        await db.commit()
        await db.refresh(child_mum)

        from app.services.case_service import get_or_assign_moderator_for_child
        assigned = await get_or_assign_moderator_for_child(db, child_mum.id)
        assert assigned is not None
        assert assigned.id == mod_mum.id
        print(f"  Mumbai child correctly assigned to Mumbai moderator: {u_mum.full_name} -> PASS")

async def test_real_chat_communication():
    print("Testing Real Child <-> Moderator Chat Messaging...")
    async with test_sessionmaker() as db:
        # Fetch existing child and moderator from earlier test
        c_res = await db.execute(select(Child).where(Child.display_name == "Priya Roy"))
        child = c_res.scalar_one_or_none()
        assert child is not None

        child_user_res = await db.execute(select(User).where(User.id == child.user_id))
        child_user = child_user_res.scalar_one_or_none()

        cases_res = await db.execute(select(Case).where(Case.child_id == child.id))
        case = cases_res.scalars().first()
        assert case is not None

        # 1. Child sends real message to active support case
        send_req = ChatMessageCreate(content="Hello inspector, someone in my class is threatening to share my photo.")
        msg_out = await chat_service.send_chat_message(db, case.id, child_user, send_req)
        assert msg_out.content == send_req.content
        assert msg_out.sender_role == "child"
        assert msg_out.is_read == False

        # 2. Verify message history retrieves it
        history = await chat_service.get_chat_history(db, case.id, child_user)
        assert len(history.messages) >= 1
        assert history.messages[-1].content == send_req.content

        # 3. Create a moderator user and reply
        mod_user_res = await db.execute(select(User).where(User.role == "moderator"))
        mod_user = mod_user_res.scalars().first()

        mod_reply = ChatMessageCreate(content="Do not panic Priya. We are taking action right now. Please do not reply to them.")
        reply_out = await chat_service.send_chat_message(db, case.id, mod_user, mod_reply)
        assert reply_out.sender_role == "moderator"

        # 4. Check unread messages can be marked read
        read_count = await chat_service.mark_messages_read(db, case.id, child_user)
        assert read_count >= 1

        print("  Child sent message, history verified, moderator replied, read receipts updated -> PASS")

async def test_claim_child_account():
    print("Testing Adult-Initiated Child Account Claiming...")
    redis_client = fake_redis.FakeRedis()
    async with test_sessionmaker() as db:
        # Create an adult-created child profile without user_id
        child_unclaimed = Child(
            protected_child_id="C-KA-BLR-CLAIM",
            display_name="Kavya",
            state="Karnataka",
            district="Bangalore",
            setup_path="ADULT_INITIATED",
            user_id=None
        )
        db.add(child_unclaimed)
        await db.commit()

        auth_service = AuthService(db, redis_client)
        claim_req = ClaimChildAccountRequest(
            email="kavya.child@student.in",
            password="Password123",
            protected_child_id="C-KA-BLR-CLAIM",
            full_name="Kavya Iyer",
            phone="9123456780"
        )
        tok = await auth_service.claim_child_account(claim_req)
        assert tok.role == "child"
        assert tok.protected_child_id == "C-KA-BLR-CLAIM"

        # Verify child is now linked to the newly created user
        await db.refresh(child_unclaimed)
        assert child_unclaimed.user_id is not None
        print(f"  Child profile claimed and user account created -> PASS")

async def main():
    print("=" * 60)
    print("RUNNING FOUNDATION HARDENING (PHASE 8.5) TEST SUITE")
    print("=" * 60)
    await init_test_db()
    await test_location_encoded_ids()
    await test_solo_domestic_danger_registration()
    await test_collaborative_adult_linked_registration()
    await test_location_priority_moderator_assignment()
    await test_real_chat_communication()
    await test_claim_child_account()
    print("=" * 60)
    print("ALL 6 TESTS PASSED! 100% SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
