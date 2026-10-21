"""
models/__init__.py
==================
Central import registry for all SQLAlchemy ORM models.

Importing all models here ensures that SQLAlchemy's mapper registry
is fully populated before Alembic runs `autogenerate` migrations.

When you add a new model file, ADD IT HERE.
"""

from app.models.auth import ConsentType, OtpLog, Role, User, UserConsent
from app.models.catalog import Crop, CropVariety, GrowthStage, Issue, Remedy
from app.models.farm import Plot, PlotCrop
from app.models.system import AuditLog, Notification, SystemFile
from app.models.diagnosis import (
    CaseAssignment,
    CaseImage,
    CaseStatusHistory,
    DiagnosisCase,
    ExpertProfile,
    ExpertReview,
)
from app.models.ai import AIModel, AIModelFeedback, AIPrediction, AIPredictionDetail
from app.models.advisory import Advisory, AdvisoryFeedback, AdvisoryTemplate

__all__ = [
    # Auth
    "Role", "User", "ConsentType", "UserConsent", "OtpLog",
    # Catalog
    "Crop", "CropVariety", "GrowthStage", "Issue", "Remedy",
    # Farm
    "Plot", "PlotCrop",
    # System
    "SystemFile", "AuditLog", "Notification",
    # Diagnosis / Case Management
    "DiagnosisCase", "CaseImage", "CaseStatusHistory",
    "ExpertProfile", "ExpertReview", "CaseAssignment",
    # AI
    "AIModel", "AIPrediction", "AIPredictionDetail", "AIModelFeedback",
    # Advisory
    "AdvisoryTemplate", "Advisory", "AdvisoryFeedback",
]
