import uuid
from datetime import datetime
from typing import Optional, Union, Dict, Any, List
from pydantic import BaseModel

class EvidenceOut(BaseModel):
    id: uuid.UUID
    incident_id: Optional[uuid.UUID] = None
    report_id: Optional[uuid.UUID] = None
    file_url: str
    file_name: str
    file_hash: str
    file_size: int
    media_type: str
    mime_type: str
    ai_processing: Optional[Union[Dict[str, Any], List[Any]]] = None
    moderator_verification: Optional[str] = None
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    provenance: Optional[Union[Dict[str, Any], List[Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EvidenceUploadResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    file_url: str
    file_hash: str
    file_size: int
    media_type: str
    mime_type: str
    message: str
