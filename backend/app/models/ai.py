"""
models/ai.py
============
SQLAlchemy ORM models for the `ai` schema.

Tables mapped here:
  - ai.models            → AIModel         (model registry)
  - ai.predictions       → AIPrediction    (prediction log)
  - ai.prediction_details → AIPredictionDetail (top-N class breakdown)
  - ai.model_feedback    → AIModelFeedback (expert ground-truth feedback)

CRITICAL INTEGRITY RULE:
  AIPrediction records are IMMUTABLE after creation.
  Never UPDATE a prediction row. Expert corrections are recorded in
  case_mgmt.expert_reviews and ai.model_feedback as separate records.
  This ensures historical AI decisions are preserved for model evaluation.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ai.models — Registry of all AI/ML model versions deployed to the system.

    Only the model where `is_active=True` is used for new predictions.
    Old model records are preserved for historical prediction auditing.

    Seeded with: 'krishibondhu-crop-vision' v1.0.0
    """
    __tablename__ = "models"
    __table_args__ = (
        UniqueConstraint("model_code", "version", name="uq_ai_model_version"),
        {"schema": "ai"},
    )

    model_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), default="PyTorch", nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), default="image_classification", nullable=False)
    accuracy_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    f1_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    artifact_path: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    predictions: Mapped[List["AIPrediction"]] = relationship("AIPrediction", back_populates="model")


class AIPrediction(Base, UUIDPrimaryKeyMixin):
    """
    ai.predictions — Log of every AI inference run on a diagnosis case image.

    Fields:
      - confidence_score : Raw probability score (0.0 to 1.0)
      - is_confident     : True if score >= settings.ai_confidence_threshold
      - raw_response     : Full JSON response from the AI service (for debugging)
      - processing_time_ms: Time taken by the AI service to process the request

    IMMUTABLE: This record is written once and never updated.
    """
    __tablename__ = "predictions"
    __table_args__ = {"schema": "ai"}

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_mgmt.diagnosis_cases.id", ondelete="CASCADE"), nullable=False)
    model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai.models.id", ondelete="RESTRICT"), nullable=False)
    file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("system.files.id", ondelete="SET NULL"))
    primary_issue_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.issues.id", ondelete="SET NULL"))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    is_confident: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_response: Mapped[Optional[Dict]] = mapped_column(JSONB)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    model: Mapped["AIModel"] = relationship("AIModel", back_populates="predictions")
    details: Mapped[List["AIPredictionDetail"]] = relationship("AIPredictionDetail", back_populates="prediction")
    case: Mapped["DiagnosisCase"] = relationship("DiagnosisCase", back_populates="predictions")
    primary_issue: Mapped[Optional["Issue"]] = relationship("Issue", foreign_keys=[primary_issue_id])


class AIPredictionDetail(Base, UUIDPrimaryKeyMixin):
    """
    ai.prediction_details — Top-N ranked class probabilities from the AI model.

    Example: The model might return top-3 guesses with confidence scores.
    These are stored here for transparency and debugging.
    """
    __tablename__ = "prediction_details"
    __table_args__ = (
        UniqueConstraint("prediction_id", "rank_order", name="uq_prediction_rank"),
        {"schema": "ai"},
    )

    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai.predictions.id", ondelete="CASCADE"), nullable=False)
    issue_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.issues.id", ondelete="SET NULL"))
    class_label: Mapped[str] = mapped_column(String(150), nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    prediction: Mapped["AIPrediction"] = relationship("AIPrediction", back_populates="details")
    issue: Mapped[Optional["Issue"]] = relationship("Issue", foreign_keys=[issue_id])


class AIModelFeedback(Base, UUIDPrimaryKeyMixin):
    """
    ai.model_feedback — Expert ground-truth validation for AI prediction quality.

    Used for model retraining and performance evaluation.
    Written when an expert submits a review that corrects the AI's prediction.
    """
    __tablename__ = "model_feedback"
    __table_args__ = {"schema": "ai"}

    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai.predictions.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_mgmt.diagnosis_cases.id", ondelete="CASCADE"), nullable=False)
    expert_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="SET NULL"))
    actual_issue_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.issues.id", ondelete="RESTRICT"))
    is_ai_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    feedback_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# Avoid circular import
from app.models.diagnosis import DiagnosisCase  # noqa: E402
from app.models.catalog import Issue  # noqa: E402
