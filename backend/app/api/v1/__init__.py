from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.children import router as children_router
from app.api.v1.adults import router as adults_router
from app.api.v1.users import router as users_router
from app.api.v1.cases import router as cases_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.reports import router as reports_router
from app.api.v1.evidence import router as evidence_router

router = APIRouter()

router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(children_router)
router.include_router(adults_router)
router.include_router(cases_router, prefix="/cases", tags=["Cases"])
router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
router.include_router(reports_router, prefix="/reports", tags=["Reports"])
router.include_router(evidence_router, prefix="/evidence", tags=["Evidence"])
