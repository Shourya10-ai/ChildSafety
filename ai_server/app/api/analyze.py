from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.pipelines.nlp.nlp_safety_pipeline import NLPSafetyPipeline
from app.risk_engine.risk_scorer import RiskScoringEngine
from app.pipelines.nlp.drift_monitor import drift_monitor

router = APIRouter()

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text snippet to analyze for child safety threats")
    context_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional caller context, e.g. user age, chat platform")

class TextAnalysisResponse(BaseModel):
    text: str
    language: str
    primary_category: str
    category_scores: Dict[str, float]
    detected_triggers: List[str]
    is_flagged: bool
    composite_risk_score: float
    risk_level: str
    confidence_score: float
    statutory_tags: List[str]
    requires_human_moderator_review: bool
    requires_immediate_sla_escalation: bool
    drift_indicators: Dict[str, Any]

class BatchAnalysisRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=50, description="Batch of texts to analyze")
    context_metadata: Optional[Dict[str, Any]] = None

class BatchAnalysisResponse(BaseModel):
    results: List[TextAnalysisResponse]
    total_analyzed: int
    flagged_count: int
    critical_count: int

class SlangRegistrationRequest(BaseModel):
    words: List[str] = Field(..., min_items=1, description="List of slang tokens to add to known vocabulary")

@router.post("/text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze single text input for cyberbullying, predatory grooming cues,
    Hinglish secrecy patterns, and self-harm intent.
    """
    raw_text = request.text
    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty or whitespace only")

    # 1. Multi-Stage NLP Detection
    nlp_res = NLPSafetyPipeline.analyze_text(raw_text)

    # 2. Risk Assessment & Statutory Tagging
    risk_res = RiskScoringEngine.calculate_risk(nlp_res)

    # 3. Concept Drift & Slang Monitoring
    drift_res = drift_monitor.record_inference(raw_text, nlp_res, risk_res)

    return TextAnalysisResponse(
        text=nlp_res["text"],
        language=nlp_res["language"],
        primary_category=nlp_res["primary_category"],
        category_scores=nlp_res["category_scores"],
        detected_triggers=nlp_res["detected_triggers"],
        is_flagged=nlp_res["is_flagged"],
        composite_risk_score=risk_res["composite_risk_score"],
        risk_level=risk_res["risk_level"],
        confidence_score=risk_res["confidence_score"],
        statutory_tags=risk_res["statutory_tags"],
        requires_human_moderator_review=risk_res["requires_human_moderator_review"],
        requires_immediate_sla_escalation=risk_res["requires_immediate_sla_escalation"],
        drift_indicators=drift_res
    )

@router.post("/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalysisRequest):
    """
    Analyze batch of messages for conversational thread audit.
    """
    results: List[TextAnalysisResponse] = []
    flagged = 0
    critical = 0

    for item in request.texts:
        if not item.strip():
            continue
        nlp_res = NLPSafetyPipeline.analyze_text(item)
        risk_res = RiskScoringEngine.calculate_risk(nlp_res)
        drift_res = drift_monitor.record_inference(item, nlp_res, risk_res)
        
        resp = TextAnalysisResponse(
            text=nlp_res["text"],
            language=nlp_res["language"],
            primary_category=nlp_res["primary_category"],
            category_scores=nlp_res["category_scores"],
            detected_triggers=nlp_res["detected_triggers"],
            is_flagged=nlp_res["is_flagged"],
            composite_risk_score=risk_res["composite_risk_score"],
            risk_level=risk_res["risk_level"],
            confidence_score=risk_res["confidence_score"],
            statutory_tags=risk_res["statutory_tags"],
            requires_human_moderator_review=risk_res["requires_human_moderator_review"],
            requires_immediate_sla_escalation=risk_res["requires_immediate_sla_escalation"],
            drift_indicators=drift_res
        )
        if resp.is_flagged:
            flagged += 1
        if resp.risk_level == "CRITICAL":
            critical += 1
        results.append(resp)

    return BatchAnalysisResponse(
        results=results,
        total_analyzed=len(results),
        flagged_count=flagged,
        critical_count=critical
    )

@router.get("/drift-metrics")
async def get_drift_metrics():
    """
    Inspect real-time OOV slang drift rate and population divergence metrics.
    """
    return drift_monitor.compute_metrics()

@router.get("/active-learning-samples")
async def get_active_learning_queue(limit: int = 20):
    """
    Inspect samples flagged for active learning / human moderator annotation.
    """
    return {
        "samples": drift_monitor.get_active_learning_samples(limit=limit),
        "total_queued": len(drift_monitor.active_learning_queue)
    }

@router.post("/register-slang")
async def register_slang(request: SlangRegistrationRequest):
    """
    Register new slang terms into the known vocabulary to adjust drift baseline.
    """
    added = drift_monitor.register_new_slang_words(request.words)
    return {
        "message": f"Successfully registered {added} new slang words",
        "vocabulary_size": len(drift_monitor.vocabulary)
    }
