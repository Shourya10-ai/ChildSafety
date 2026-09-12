from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.analyze import router as analyze_router
from app.api.rag import router as rag_router
from app.models.model_registry import ModelRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ModelRegistry on startup...")
    registry = ModelRegistry()
    yield
    logger.info("Cleaning up ModelRegistry on shutdown...")
    # Optionally unload all to free memory on shutdown

app = FastAPI(title='Child Safety AI Server', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(analyze_router, prefix="/api/v1/analyze", tags=["Safety Analysis"])
app.include_router(rag_router, prefix="/api/v1/rag", tags=["Statutory Legal RAG"])
