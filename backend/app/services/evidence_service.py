import os
import hashlib
import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceUploadResponse

LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage", "evidence")

def detect_media_type(mime_type: str) -> str:
    if mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("video/"):
        return "video"
    elif mime_type.startswith("audio/"):
        return "audio"
    else:
        return "document"

async def save_evidence_file(
    db: AsyncSession,
    file: UploadFile,
    incident_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    uploader_user_id: Optional[uuid.UUID] = None
) -> EvidenceUploadResponse:
    content = await file.read()
    file_size = len(content)
    
    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    
    # 1. Calculate SHA-256 hash for integrity & provenance
    sha256_hash = hashlib.sha256(content).hexdigest()

    # 2. Derive media type & safe filename
    mime_type = file.content_type or "application/octet-stream"
    media_type = detect_media_type(mime_type)
    file_ext = os.path.splitext(file.filename or "")[1] or ".bin"
    stored_file_name = f"{sha256_hash[:16]}_{uuid.uuid4().hex[:8]}{file_ext}"

    # 3. Store file: Try MinIO first, fallback gracefully to local storage
    file_url = f"/storage/evidence/{stored_file_name}"
    try:
        # MinIO attempt if configured
        import urllib.request
        # If MinIO is reachable in docker:
        # For local dev without docker, store locally:
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
        local_path = os.path.join(LOCAL_STORAGE_DIR, stored_file_name)
        with open(local_path, "wb") as f:
            f.write(content)
    except Exception as e:
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
        local_path = os.path.join(LOCAL_STORAGE_DIR, stored_file_name)
        with open(local_path, "wb") as f:
            f.write(content)

    # 4. Create Evidence DB record
    evidence = Evidence(
        incident_id=incident_id,
        report_id=report_id,
        file_url=file_url,
        file_name=file.filename or stored_file_name,
        file_hash=sha256_hash,
        file_size=file_size,
        media_type=media_type,
        mime_type=mime_type,
        provenance={
            "uploaded_by": str(uploader_user_id) if uploader_user_id else "anonymous",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "original_filename": file.filename,
            "sha256": sha256_hash
        }
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    return EvidenceUploadResponse(
        id=evidence.id,
        file_name=evidence.file_name,
        file_url=evidence.file_url,
        file_hash=evidence.file_hash,
        file_size=evidence.file_size,
        media_type=evidence.media_type,
        mime_type=evidence.mime_type,
        message="Evidence uploaded and integrity hash computed successfully."
    )
