from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.dependencies import get_db, get_redis
import redis.asyncio as redis

router = APIRouter()

@router.get("/")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    services_status = {"database": False, "redis": False}
    
    try:
        await db.execute(text("SELECT 1"))
        services_status["database"] = True
    except Exception:
        pass
        
    try:
        await redis_client.ping()
        services_status["redis"] = True
    except Exception:
        pass

    status = "healthy" if all(services_status.values()) else "degraded"
    
    return {
        "status": status,
        "version": "0.1.0",
        "services": services_status
    }
