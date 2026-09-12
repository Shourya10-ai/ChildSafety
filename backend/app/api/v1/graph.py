import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.schemas.knowledge_graph import (
    GraphDataResponse,
    ConnectTheDotsResponse,
    PredatoryClustersResponse,
    GraphStatsResponse,
    LinkSuspectRequest,
    SuspectEntityOut
)
from app.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter(prefix="/graph", tags=["Knowledge Graph & Case Intelligence"])

@router.get("/case/{case_id}", response_model=GraphDataResponse)
async def get_case_subgraph(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Returns an interactive multi-hop ego-graph for a case showing connected victims,
    incidents, suspect handles/platforms, geographic anchors, and cross-case links.
    """
    return await KnowledgeGraphService.build_graph_for_case(db, case_id)

@router.get("/connect-the-dots", response_model=ConnectTheDotsResponse)
async def connect_the_dots(
    identifier: str = Query(..., description="Suspect handle, phone number, or digital ID to trace"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Cross-case connect-the-dots lookup: Traces every victim child, case, and jurisdiction
    touching an offender handle or phone number.
    """
    return await KnowledgeGraphService.connect_the_dots(db, identifier)

@router.get("/clusters", response_model=PredatoryClustersResponse)
async def list_predatory_clusters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Surfaces serial offenders and multi-victim predatory clusters across districts and states.
    """
    return await KnowledgeGraphService.find_predatory_clusters(db)

@router.get("/stats", response_model=GraphStatsResponse)
async def get_knowledge_graph_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Returns platform-wide knowledge graph statistics including node counts and multi-victim clusters.
    """
    return await KnowledgeGraphService.get_graph_statistics(db)

@router.post("/link-suspect", response_model=SuspectEntityOut, status_code=status.HTTP_201_CREATED)
async def link_suspect_to_incident(
    req: LinkSuspectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Associates an online suspect handle/phone/gaming tag with an incident and Modus Operandi.
    """
    try:
        return await KnowledgeGraphService.link_suspect_to_incident(db, req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
