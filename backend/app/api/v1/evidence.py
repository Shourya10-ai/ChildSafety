import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.evidence import EvidenceUploadResponse
from app.services import evidence_service

router = APIRouter()

@router.post("/upload", response_model=EvidenceUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    incident_id: Optional[uuid.UUID] = Form(None),
    report_id: Optional[uuid.UUID] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Uploads evidence (screenshot, audio, document), calculates SHA-256 hash,
    stores in MinIO / local storage, and tracks provenance.
    """
    return await evidence_service.save_evidence_file(
        db=db,
        file=file,
        incident_id=incident_id,
        report_id=report_id,
        uploader_user_id=current_user.id,
        uploader_role=current_user.role
    )

@router.get("/{id}/verify-custody")
async def verify_chain_of_custody(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verifies mathematical SHA-256 block-linked integrity of evidence chain of custody
    under Section 63 Bharatiya Sakshya Adhiniyam, 2023.
    """
    return await evidence_service.verify_evidence_chain_of_custody(db, id)

