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
from app.api.v1.sos import router as sos_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.consent import router as consent_router
from app.api.v1.chat import router as chat_router
from app.api.v1.missing_children import router as missing_children_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.dpdp import router as dpdp_router
from app.api.v1.graph import router as graph_router
from app.api.v1.risk import router as risk_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.speech import router as speech_router
from app.api.v1.ws import router as ws_router

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
router.include_router(sos_router, prefix="/sos", tags=["SOS"])
router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
router.include_router(consent_router, prefix="/consent", tags=["Parental Consent"])
router.include_router(chat_router)
router.include_router(missing_children_router)
router.include_router(intelligence_router)
router.include_router(dpdp_router)
router.include_router(graph_router)
router.include_router(risk_router)
router.include_router(copilot_router, prefix="/copilot", tags=["AI Copilot & Legal RAG"])
router.include_router(speech_router, prefix="/speech", tags=["Speech & Voice Reporting"])
router.include_router(ws_router, tags=["WebSocket Gateway"])

