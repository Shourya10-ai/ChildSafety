from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router

router = APIRouter()
router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(auth_router)
