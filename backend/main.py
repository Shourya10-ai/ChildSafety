from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.session import init_db
from app.api.v1 import router as api_v1_router
from app.core.config import settings
import redis.asyncio as redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    await init_db()
    
    # Initialize Redis connection test
    redis_client = redis.from_url(settings.REDIS_URL)
    await redis_client.ping()
    await redis_client.close()
    
    yield
    # Cleanup on shutdown

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
