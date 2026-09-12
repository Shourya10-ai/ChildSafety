from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.speech import TranscriptionResponse, VoiceReportResponse
from app.services.speech_service import SpeechService

router = APIRouter()

@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe audio recording to text with safety threat classification"
)
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts an uploaded audio file (WAV, M4A, MP3, OGG, WebM) and returns
    transcription, detected safety keywords, and threat level.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file uploaded")
    try:
        return await SpeechService.transcribe_audio(audio_bytes, file.filename or "audio_recording.wav")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Transcription failed: {str(e)}")

@router.post(
    "/voice-report",
    response_model=VoiceReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="1-Tap Voice Incident Reporting"
)
async def submit_voice_incident_report(
    file: UploadFile = File(...),
    platform: Optional[str] = Form("Other"),
    category: Optional[str] = Form(None),
    child_id: Optional[uuid.UUID] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    1-Tap Voice Reporting: Ingests a voice note, transcribes speech, classifies threat,
    creates a safety report, and attaches it to an active case file.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio recording uploaded")
    try:
        return await SpeechService.submit_voice_report(
            db=db,
            audio_bytes=audio_bytes,
            filename=file.filename or "voice_report.wav",
            reporter_user_id=current_user.id,
            reporter_role=current_user.role,
            child_id=child_id,
            platform=platform,
            category_hint=category
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Voice report submission failed: {str(e)}")
