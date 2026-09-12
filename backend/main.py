from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.session import init_db
from app.api.v1 import router as api_v1_router
from app.core.config import settings
import redis.asyncio as redis

import asyncio
from app.core.websocket_manager import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    await init_db()
    
    # Initialize Redis connection test
    redis_client = redis.from_url(settings.REDIS_URL)
    try:
        await redis_client.ping()
        ws_manager._listener_task = asyncio.create_task(ws_manager.start_redis_listener(redis_client))
    except Exception as e:
        print(f"Redis not available: {e}")
        await redis_client.close()
    
    yield
    # Cleanup on shutdown
    if getattr(ws_manager, "_listener_task", None):
        ws_manager._listener_task.cancel()
    await redis_client.close()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
