"""
schemas/diagnosis.py
====================
Pydantic v2 schemas for diagnosis case, AI analysis, and advisory response endpoints.
"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ─────────────────────────────────────────────────────────
# Diagnosis Case Creation
# ─────────────────────────────────────────────────────────

class CreateDiagnosisCaseRequest(BaseModel):
    """
    POST /api/v1/diagnosis-cases

    Creates a DRAFT case. The farmer provides crop context and initial notes.
    Images are attached separately via POST /api/v1/diagnosis-cases/{id}/images.
    Analysis is triggered via POST /api/v1/diagnosis-cases/{id}/analyze.
    """
    crop_id: UUID = Field(..., description="Which crop has the problem?")
    growth_stage_id: Optional[UUID] = Field(None, description="Current growth stage of the crop")
    plot_id: Optional[UUID] = Field(None, description="Which plot is affected?")
    plot_crop_id: Optional[UUID] = None
    farmer_id: Optional[UUID] = Field(None, description="Target farmer ID if created on behalf by agent or admin")
    farmer_notes: Optional[str] = Field(None, max_length=2000, description="Farmer's description of symptoms")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)


class AttachCaseImageRequest(BaseModel):
    """
    POST /api/v1/diagnosis-cases/{case_id}/images

    Attach an already-uploaded file (from the /files flow) to a case.
    """
    file_id: UUID = Field(..., description="ID of the uploaded file (from /files/confirm-upload)")
    image_type: str = Field(default="leaf", description="Type: leaf | stem | fruit | root | whole_plant")
    is_primary: bool = Field(default=False, description="Is this the main image for AI analysis?")


# ─────────────────────────────────────────────────────────
# AI Prediction / Advisory Response
# ─────────────────────────────────────────────────────────

class PredictionDetailResponse(BaseModel):
    """A single ranked AI class prediction."""
    rank: int
    class_label: str
    confidence_score: float
    issue_id: Optional[UUID] = None


class AdvisoryPayloadResponse(BaseModel):
    """
    The Bangla advisory content returned after a successful AI diagnosis.
    Formatted for display AND for browser Text-to-Speech (audio_text_bn).
    """
    title_bn: str
    summary_bn: str
    detailed_treatment_bn: str
    preventive_measures_bn: Optional[str] = None
    chemical_recommendations_bn: Optional[str] = None
    organic_recommendations_bn: Optional[str] = None
    source: str  # 'ai_generated' | 'expert_approved' | 'expert_overridden'


class DiagnosisResponse(BaseModel):
    """
    Returned by GET and POST .../analyze — the full diagnosis result.

    `confidence_level` is a human-friendly label derived from the numeric score:
      - high   : >= 85%
      - medium : >= 65%
      - low    : < 65% (triggers expert escalation)

    `requires_expert_review` will be True when confidence is low.
    In that case, `advisory` will be None (we don't show unverified advice).
    """
    model_config = ConfigDict(from_attributes=True)

    case_id: UUID
    case_number: str
    case_status: str
    urgency_level: str

    # AI Diagnosis
    issue_id: Optional[UUID] = None
    issue_name_bn: Optional[str] = None
    issue_name_en: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None   # 'high' | 'medium' | 'low'
    requires_expert_review: bool = False

    # Top-N AI alternatives
    top_predictions: List[PredictionDetailResponse] = []

    # Advisory (None if requires_expert_review=True)
    advisory: Optional[AdvisoryPayloadResponse] = None


class CaseListResponse(BaseModel):
    """Lightweight case summary for listing farmer's case history."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_number: str
    status: str
    urgency_level: str
    crop_id: Optional[UUID] = None
    created_at: str  # ISO timestamp string


# ─────────────────────────────────────────────────────────
# Expert Review
# ─────────────────────────────────────────────────────────

class SubmitExpertReviewRequest(BaseModel):
    """
    POST /api/v1/expert/cases/{case_id}/review

    Expert submits their diagnosis review. This creates a NEW record
    and NEVER modifies the original AI prediction.
    """
    agreed_with_ai: bool = Field(..., description="Does the expert agree with the AI's top prediction?")
    verified_issue_id: Optional[UUID] = Field(None, description="The expert's confirmed issue ID (required if agreed_with_ai=False)")
    diagnosis_notes_bn: str = Field(..., min_length=10, description="Expert's diagnosis notes in Bangla")
    diagnosis_notes_en: Optional[str] = None
    prescribed_treatment_bn: Optional[str] = Field(None, description="Expert's treatment prescription in Bangla")

    @model_validator(mode="after")
    def validate_verified_issue_when_disagreeing(self):
        if not self.agreed_with_ai and not self.verified_issue_id:
            raise ValueError("AI-এর সাথে দ্বিমত পোষণ করলে সঠিক রোগ (verified_issue_id) উল্লেখ করা বাধ্যতামূলক।")
        return self


class ExpertReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    case_id: UUID
    expert_id: UUID
    agreed_with_ai: bool
    verified_issue_id: Optional[UUID] = None
    diagnosis_notes_bn: str
    review_status: str
    reviewed_at: str


# ─────────────────────────────────────────────────────────
# Farmer Feedback
# ─────────────────────────────────────────────────────────

class SubmitFeedbackRequest(BaseModel):
    """POST /api/v1/diagnosis-cases/{case_id}/feedback"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_helpful: Optional[bool] = None
    feedback_text: Optional[str] = Field(None, max_length=1000)
    outcome_status: Optional[str] = Field(None, description="resolved | partially_resolved | ineffective")
