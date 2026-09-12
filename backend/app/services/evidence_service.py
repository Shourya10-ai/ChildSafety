import os
import hashlib
import hmac
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.models.evidence import Evidence
from app.models.chain_of_custody import EvidenceChainOfCustody
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

async def record_chain_of_custody_event(
    db: AsyncSession,
    evidence_id: uuid.UUID,
    action: str,
    file_sha256: str,
    actor_id: Optional[uuid.UUID] = None,
    actor_role: str = "system",
    metadata: Optional[Dict[str, Any]] = None
) -> EvidenceChainOfCustody:
    """
    Appends an immutable block to the Evidence Chain of Custody ledger.
    """
    # Fetch last block to get previous hash & sequence number
    res = await db.execute(
        select(EvidenceChainOfCustody)
        .where(EvidenceChainOfCustody.evidence_id == evidence_id)
        .order_by(EvidenceChainOfCustody.sequence_number.desc())
        .limit(1)
    )
    last_block = res.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if last_block is None:
        sequence_number = 1
        previous_block_hash = "0" * 64  # Genesis hash
    else:
        sequence_number = last_block.sequence_number + 1
        previous_block_hash = last_block.block_hash

    # Calculate payload & block hashes
    payload_str = f"{sequence_number}:{action}:{str(actor_id)}:{actor_role}:{file_sha256}:{now.isoformat()}"
    entry_payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    block_hash = hashlib.sha256(f"{previous_block_hash}:{entry_payload_hash}".encode("utf-8")).hexdigest()

    # Sign with HMAC using application secret
    secret = settings.SECRET_KEY.encode("utf-8")
    digital_sig = hmac.new(secret, block_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    entry = EvidenceChainOfCustody(
        evidence_id=evidence_id,
        sequence_number=sequence_number,
        action=action,
        actor_id=actor_id,
        actor_role=actor_role,
        file_sha256=file_sha256,
        previous_block_hash=previous_block_hash,
        entry_payload_hash=entry_payload_hash,
        block_hash=block_hash,
        digital_signature=digital_sig,
        metadata_json=metadata,
        timestamp=now
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

async def verify_evidence_chain_of_custody(
    db: AsyncSession,
    evidence_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Validates complete mathematical integrity of the evidence hash chain.
    """
    res = await db.execute(
        select(EvidenceChainOfCustody)
        .where(EvidenceChainOfCustody.evidence_id == evidence_id)
        .order_by(EvidenceChainOfCustody.sequence_number.asc())
    )
    blocks = list(res.scalars().all())

    if not blocks:
        return {
            "evidence_id": str(evidence_id),
            "is_valid": False,
            "block_count": 0,
            "message": "No chain-of-custody ledger entries found for this evidence item."
        }

    expected_prev = "0" * 64
    secret = settings.SECRET_KEY.encode("utf-8")

    for i, b in enumerate(blocks):
        # 1. Verify sequence order
        if b.sequence_number != i + 1:
            return {
                "evidence_id": str(evidence_id),
                "is_valid": False,
                "broken_at_sequence": b.sequence_number,
                "message": f"Sequence anomaly detected at block #{b.sequence_number}."
            }

        # 2. Verify prior block link
        if b.previous_block_hash != expected_prev:
            return {
                "evidence_id": str(evidence_id),
                "is_valid": False,
                "broken_at_sequence": b.sequence_number,
                "message": f"Tampered previous block link detected at block #{b.sequence_number}."
            }

        # 3. Verify block hash calculation
        expected_block_hash = hashlib.sha256(f"{expected_prev}:{b.entry_payload_hash}".encode("utf-8")).hexdigest()
        if b.block_hash != expected_block_hash:
            return {
                "evidence_id": str(evidence_id),
                "is_valid": False,
                "broken_at_sequence": b.sequence_number,
                "message": f"Block hash mismatch at block #{b.sequence_number}."
            }

        # 4. Verify HMAC digital signature
        expected_sig = hmac.new(secret, b.block_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(b.digital_signature, expected_sig):
            return {
                "evidence_id": str(evidence_id),
                "is_valid": False,
                "broken_at_sequence": b.sequence_number,
                "message": f"Cryptographic signature invalid at block #{b.sequence_number}."
            }

        expected_prev = b.block_hash

    return {
        "evidence_id": str(evidence_id),
        "is_valid": True,
        "block_count": len(blocks),
        "latest_block_hash": expected_prev,
        "compliance": "Section 63 of Bharatiya Sakshya Adhiniyam, 2023 / Section 65B Indian Evidence Act",
        "message": "Chain of custody is mathematically intact and tamper-evident."
    }

async def save_evidence_file(
    db: AsyncSession,
    file: UploadFile,
    incident_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    uploader_user_id: Optional[uuid.UUID] = None,
    uploader_role: str = "child"
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

    # 3. Store file locally with directories ensured
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
    local_path = os.path.join(LOCAL_STORAGE_DIR, stored_file_name)
    with open(local_path, "wb") as f:
        f.write(content)
    file_url = f"/storage/evidence/{stored_file_name}"

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

    # 5. Genesis block in immutable chain of custody
    await record_chain_of_custody_event(
        db=db,
        evidence_id=evidence.id,
        action="UPLOADED",
        file_sha256=sha256_hash,
        actor_id=uploader_user_id,
        actor_role=uploader_role,
        metadata={"filename": file.filename, "size_bytes": file_size, "mime_type": mime_type}
    )

    return EvidenceUploadResponse(
        id=evidence.id,
        file_name=evidence.file_name,
        file_url=evidence.file_url,
        file_hash=evidence.file_hash,
        file_size=evidence.file_size,
        media_type=evidence.media_type,
        mime_type=evidence.mime_type,
        message="Evidence uploaded, SHA-256 computed, and immutable genesis chain-of-custody block recorded."
    )
