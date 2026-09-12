"""
Standalone local development runner for Child Safety Platform Backend.
Enables immediate testing from physical Android phone or browser.
Automatically falls back to local SQLite + in-memory Redis if PostgreSQL/Redis aren't running.
"""
import asyncio
import os
import sys

# Ensure backend root is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.base import Base
from app.api.v1 import router as api_v1_router
from app.models.user import User
from app.models.child import Child, Adult, AdultChildLink
from app.models.moderator import Moderator, Assignment
from app.models.identity_vault import IdentityVault
from app.models.case import Case, Incident, Report, ModeratorNote
from app.models.evidence import Evidence
from app.models.sos import SOSEvent
from app.models.notification import Notification, ChatMessage
from app.models.escalation import Escalation
from app.models.audit import AuditLog
from app.models.chain_of_custody import EvidenceChainOfCustody
from app.models.parental_consent import ParentalConsent

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import app.db.session as db_session_module
import app.core.dependencies as deps_module
import redis.asyncio as redis

# Setup local SQLite database for instant zero-dependency testing
LOCAL_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_dev.db")
SQLITE_URL = f"sqlite+aiosqlite:///{LOCAL_DB_FILE}"

dev_engine = create_async_engine(
    SQLITE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)
dev_sessionmaker = async_sessionmaker(dev_engine, class_=AsyncSession, expire_on_commit=False)

# Monkey-patch sessionmaker for local dev
db_session_module.async_session_maker = dev_sessionmaker
db_session_module.engine = dev_engine

async def override_get_db():
    async with dev_sessionmaker() as session:
        yield session

# Fake/In-memory redis client for local dev
try:
    import fakeredis.aioredis as fake_redis
    fake_redis_client = fake_redis.FakeRedis()
except Exception:
    fake_redis_client = None

async def override_get_redis():
    if fake_redis_client is not None:
        yield fake_redis_client
    else:
        client = redis.from_url(settings.REDIS_URL)
        try:
            yield client
        finally:
            await client.close()

from app.core.dependencies import get_db as orig_get_db, get_redis as orig_get_redis

@asynccontextmanager
async def dev_lifespan(app: FastAPI):
    print("=" * 60)
    print("CHILD SAFETY PLATFORM -- LOCAL DEV SERVER")
    print("Listening on: 0.0.0.0:8000")
    print("Phone (USB Tethering) Target: http://10.147.167.171:8000/")
    print("Browser Swagger UI: http://localhost:8000/docs")
    print("=" * 60)
    
    # Create tables safely for local dev
    tables_to_create = [
        User.__table__,
        Child.__table__,
        Adult.__table__,
        AdultChildLink.__table__,
        Moderator.__table__,
        Assignment.__table__,
        IdentityVault.__table__,
        Case.__table__,
        Incident.__table__,
        Report.__table__,
        ModeratorNote.__table__,
        Evidence.__table__,
        SOSEvent.__table__,
        Notification.__table__,
        ChatMessage.__table__,
        Escalation.__table__,
        AuditLog.__table__,
        EvidenceChainOfCustody.__table__,
        ParentalConsent.__table__,
    ]
    async with dev_engine.begin() as conn:
        for tbl in tables_to_create:
            try:
                await conn.run_sync(tbl.create, checkfirst=True)
            except Exception as e:
                print(f"Notice creating {tbl.name}: {e}")
    print("Local database tables ready (Auth, Users, Children, Adults, Cases, Chat).")
    
    yield
    await dev_engine.dispose()

app = FastAPI(title="Child Safety Platform (Local Dev)", lifespan=dev_lifespan)

app.dependency_overrides[orig_get_db] = override_get_db
app.dependency_overrides[orig_get_redis] = override_get_redis

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "online", "message": "Child Safety Platform Backend is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
