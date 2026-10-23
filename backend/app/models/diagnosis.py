"""
models/diagnosis.py
===================
SQLAlchemy ORM models for the `case_mgmt` schema.

Tables mapped here:
  - case_mgmt.diagnosis_cases     → DiagnosisCase
  - case_mgmt.case_images         → CaseImage
  - case_mgmt.case_status_history → CaseStatusHistory
  - case_mgmt.expert_profiles     → ExpertProfile
  - case_mgmt.expert_reviews      → ExpertReview
  - case_mgmt.case_assignments    → CaseAssignment

DiagnosisCase is the central entity of the ChashiGuard (ফসল রক্ষক) flow.
It links a farmer's submission to AI predictions and expert reviews.

Status lifecycle:
  submitted → processing → ai_analyzed → escalated → expert_reviewed → closed
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DiagnosisCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    case_mgmt.diagnosis_cases — A single crop disease inquiry submitted by a farmer.

    The `case_number` is a human-readable ID (e.g., KB-2026-000124) generated
    by a database sequence trigger (see 013_indexes_and_triggers.sql).
    """
    __tablename__ = "diagnosis_cases"
    __table_args__ = {"schema": "case_mgmt"}

    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    plot_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("farm.plots.id", ondelete="SET NULL"))
    plot_crop_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("farm.plot_crops.id", ondelete="SET NULL"))
    crop_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.crops.id", ondelete="RESTRICT"))
    growth_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.growth_stages.id", ondelete="SET NULL"))

    # Primary image for AI analysis
    primary_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("system.files.id", ondelete="SET NULL"))
    voice_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("system.files.id", ondelete="SET NULL"))

    farmer_notes: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8))

    # Case lifecycle
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False)
    urgency_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    assigned_expert_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="SET NULL"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    images: Mapped[List["CaseImage"]] = relationship("CaseImage", back_populates="case")
    status_history: Mapped[List["CaseStatusHistory"]] = relationship("CaseStatusHistory", back_populates="case", order_by="CaseStatusHistory.created_at")
    predictions: Mapped[List["AIPrediction"]] = relationship("AIPrediction", back_populates="case", order_by="AIPrediction.created_at")
    advisory: Mapped[Optional["Advisory"]] = relationship("Advisory", back_populates="case", uselist=False)
    expert_reviews: Mapped[List["ExpertReview"]] = relationship("ExpertReview", back_populates="case", order_by="ExpertReview.reviewed_at")


class CaseImage(Base, UUIDPrimaryKeyMixin):
    """
    case_mgmt.case_images — Additional images attached to a diagnosis case.
    Multiple angles (leaf, stem, fruit, root, whole_plant) can be uploaded.
    """
    __tablename__ = "case_images"
    __table_args__ = {"schema": "case_mgmt"}

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_mgmt.diagnosis_cases.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("system.files.id", ondelete="CASCADE"), nullable=False)
    image_type: Mapped[str] = mapped_column(String(50), default="leaf", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped["DiagnosisCase"] = relationship("DiagnosisCase", back_populates="images")
    file: Mapped["SystemFile"] = relationship("SystemFile", foreign_keys=[file_id])


class CaseStatusHistory(Base, UUIDPrimaryKeyMixin):
    """
    case_mgmt.case_status_history — Immutable log of every status change on a case.
    Allows full audit of how a case progressed through its lifecycle.
    """
    __tablename__ = "case_status_history"
    __table_args__ = {"schema": "case_mgmt"}

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_mgmt.diagnosis_cases.id", ondelete="CASCADE"), nullable=False)
    previous_status: Mapped[Optional[str]] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="SET NULL"))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped["DiagnosisCase"] = relationship("DiagnosisCase", back_populates="status_history")


class ExpertProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    case_mgmt.expert_profiles — Extended profile for users with 'expert' role.
    Tracks availability, specialization, and workload capacity.
    """
    __tablename__ = "expert_profiles"
    __table_args__ = {"schema": "case_mgmt"}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), unique=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(150), nullable=False)
    organization: Mapped[str] = mapped_column(String(200), nullable=False)
    specialization_notes: Mapped[Optional[str]] = mapped_column(Text)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_active_cases: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), default=5.00)


class ExpertReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    case_mgmt.expert_reviews — An expert's diagnosis and treatment recommendation.

    CRITICAL RULE: Expert reviews are ALWAYS new INSERT records.
    The original AI prediction (ai.predictions) is NEVER overwritten.
    This preserves data integrity and enables AI model improvement feedback loops.

    `agreed_with_ai`: True if expert agrees with AI diagnosis.
    `verified_issue_id`: The expert's confirmed issue (may differ from AI's).
    """
    __tablename__ = "expert_reviews"
    __table_args__ = {"schema": "case_mgmt"}

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_mgmt.diagnosis_cases.id", ondelete="CASCADE"), nullable=False)
    expert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="RESTRICT"), nullable=False)
    agreed_with_ai: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verified_issue_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.issues.id", ondelete="RESTRICT"))
    diagnosis_notes_bn: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis_notes_en: Mapped[Optional[str]] = mapped_column(Text)
    prescribed_treatment_bn: Mapped[Optional[str]] = mapped_column(Text)
    voice_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("system.files.id", ondelete="SET NULL"))
    review_status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped["DiagnosisCase"] = relationship("DiagnosisCase", back_populates="expert_reviews")
    expert: Mapped[Optional["User"]] = relationship("User", foreign_keys=[expert_id])


class CaseAssignment(Base, UUIDPrimaryKeyMixin):
    """
    case_mgmt.case_assignments — Assignment of a case to an expert for review.
    """
    __tablename__ = "case_assignments"
    __table_args__ = {"schema": "case_mgmt"}

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_mgmt.diagnosis_cases.id", ondelete="CASCADE"), nullable=False)
    expert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="RESTRICT"), nullable=False)
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), default="assigned", nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    decline_reason: Mapped[Optional[str]] = mapped_column(Text)


# Import here to avoid circular imports with advisory.py
from app.models.ai import AIPrediction  # noqa: E402
from app.models.advisory import Advisory  # noqa: E402
from app.models.system import SystemFile  # noqa: E402
from app.models.auth import User  # noqa: E402
