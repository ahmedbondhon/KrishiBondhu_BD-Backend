"""
models/advisory.py
==================
SQLAlchemy ORM models for the `advisory` schema.

Tables mapped here:
  - advisory.templates  → AdvisoryTemplate  (master Bangla advice content)
  - advisory.advisories → Advisory          (per-case generated advisory)
  - advisory.feedbacks  → AdvisoryFeedback  (farmer outcome feedback)

The Advisory Engine works as follows:
  1. After AI diagnosis with high/medium confidence, the engine queries
     advisory.templates matching (issue_id, growth_stage_id, severity_level).
  2. A new Advisory record is created for that case.
  3. The farmer receives the advisory in Bangla (and audio text for TTS).
  4. After applying the advice, the farmer can submit an AdvisoryFeedback.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdvisoryTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    advisory.templates — Master Bangla advisory content for each (issue, stage, severity) combination.

    Content fields:
      - title_bn            : Short advisory headline in Bangla
      - content_bn          : Full treatment instructions in Bangla
      - preventive_measures_bn : How to prevent this issue in the future
      - safety_precautions_bn  : Chemical safety warnings in Bangla
    """
    __tablename__ = "templates"
    __table_args__ = {"schema": "advisory"}

    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.issues.id", ondelete="CASCADE"), nullable=False)
    growth_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.growth_stages.id", ondelete="SET NULL"))
    severity_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)

    title_bn: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(255))
    content_bn: Mapped[str] = mapped_column(Text, nullable=False)
    content_en: Mapped[Optional[str]] = mapped_column(Text)
    preventive_measures_bn: Mapped[Optional[str]] = mapped_column(Text)
    safety_precautions_bn: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Advisory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    advisory.advisories — The generated advisory for a specific diagnosis case.

    One advisory per case (enforced by UNIQUE constraint on case_id).

    `source` tracks the provenance of the advisory:
      - 'ai_generated'    : Generated from template after AI prediction
      - 'expert_approved' : Expert reviewed and approved the AI advisory
      - 'expert_overridden': Expert replaced the AI advisory with their own
    """
    __tablename__ = "advisories"
    __table_args__ = {"schema": "advisory"}

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_mgmt.diagnosis_cases.id", ondelete="CASCADE"), unique=True, nullable=False)
    prediction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ai.predictions.id", ondelete="SET NULL"))
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("advisory.templates.id", ondelete="SET NULL"))

    title_bn: Mapped[str] = mapped_column(String(255), nullable=False)
    summary_bn: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_treatment_bn: Mapped[str] = mapped_column(Text, nullable=False)
    preventive_measures_bn: Mapped[Optional[str]] = mapped_column(Text)
    chemical_recommendations_bn: Mapped[Optional[str]] = mapped_column(Text)
    organic_recommendations_bn: Mapped[Optional[str]] = mapped_column(Text)

    audio_advisory_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("system.files.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(50), default="ai_generated", nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="SET NULL"))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["DiagnosisCase"] = relationship("DiagnosisCase", back_populates="advisory")
    feedbacks: Mapped[list["AdvisoryFeedback"]] = relationship("AdvisoryFeedback", back_populates="advisory")


class AdvisoryFeedback(Base, UUIDPrimaryKeyMixin):
    """
    advisory.feedbacks — Farmer's outcome feedback after applying an advisory.

    Rating (1-5 stars) and `is_helpful` flag help measure advisory effectiveness.
    `outcome_status` tracks whether the advice worked: resolved, partial, ineffective.
    """
    __tablename__ = "feedbacks"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating"),
        {"schema": "advisory"},
    )

    advisory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("advisory.advisories.id", ondelete="CASCADE"), nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer)
    is_helpful: Mapped[Optional[bool]] = mapped_column(Boolean)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text)
    audio_feedback_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("system.files.id", ondelete="SET NULL"))
    outcome_status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    advisory: Mapped["Advisory"] = relationship("Advisory", back_populates="feedbacks")


# Avoid circular import
from app.models.diagnosis import DiagnosisCase  # noqa: E402
