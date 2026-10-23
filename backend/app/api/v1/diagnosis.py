"""
api/v1/diagnosis.py
===================
HTTP route handlers for the ChashiGuard crop diagnosis flow.

Routes (Farmer-facing):
  POST /api/v1/diagnosis-cases                      → Create a new draft case
  POST /api/v1/diagnosis-cases/{case_id}/images     → Attach image to case
  POST /api/v1/diagnosis-cases/{case_id}/analyze    → Trigger AI analysis
  GET  /api/v1/diagnosis-cases/{case_id}            → View diagnosis result
  GET  /api/v1/diagnosis-cases                      → List farmer's case history
  POST /api/v1/diagnosis-cases/{case_id}/request-expert-review → Request human expert
  POST /api/v1/diagnosis-cases/{case_id}/feedback   → Submit outcome feedback

Routes (Expert-facing):
  GET  /api/v1/expert/cases                        → Get pending cases queue
  POST /api/v1/expert/cases/{case_id}/review       → Submit expert review
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, get_db, require_roles
from app.core.responses import success_response
from app.models.advisory import Advisory
from app.models.ai import AIPrediction
from app.models.auth import User
from app.models.catalog import Issue
from app.models.diagnosis import CaseAssignment, DiagnosisCase
from app.schemas.diagnosis import (
    AttachCaseImageRequest,
    CreateDiagnosisCaseRequest,
    ExpertReviewResponse,
    SubmitExpertReviewRequest,
    SubmitFeedbackRequest,
)
from app.services.diagnosis_service import DiagnosisService, _confidence_label, diagnosis_service

router = APIRouter(tags=["Crop Diagnosis (ChashiGuard)"])
expert_router = APIRouter(prefix="/expert", tags=["Expert Review Workflow"])


# ─────────────────────────────────────────────────────────
# Farmer Routes
# ─────────────────────────────────────────────────────────

@router.post("/diagnosis-cases", status_code=201, summary="Create a new crop diagnosis case")
async def create_diagnosis_case(
    payload: CreateDiagnosisCaseRequest,
    current_user: User = Depends(require_roles("farmer", "agent")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a draft diagnosis case. A case number (e.g., KB-2026-000124) is auto-generated.

    After creation:
      1. Attach at least one image via POST /diagnosis-cases/{case_id}/images
      2. Trigger analysis via POST /diagnosis-cases/{case_id}/analyze
    """
    target_farmer_id = current_user.id
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if current_user.role else "")
    if user_role in ("agent", "admin", "administrator", "tech_admin", "technical_admin") and payload.farmer_id:
        target_farmer_id = payload.farmer_id

    case = await diagnosis_service.create_case(db, target_farmer_id, payload)
    return success_response(
        data={"case_id": str(case.id), "case_number": case.case_number, "status": case.status},
        message="রোগ নির্ণয় কেস তৈরি হয়েছে।",
        status_code=201,
    )


@router.post(
    "/diagnosis-cases/{case_id}/images",
    status_code=201,
    summary="Attach an uploaded image to a diagnosis case",
)
async def attach_image(
    case_id: UUID,
    payload: AttachCaseImageRequest,
    current_user: User = Depends(require_roles("farmer", "agent")),
    db: AsyncSession = Depends(get_db),
):
    """
    Attach a file (already uploaded via /files flow) to a diagnosis case.
    The `is_primary=True` image will be used for AI analysis.
    """
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    image = await diagnosis_service.attach_image(db, case_id, current_user.id, payload, user_role=user_role)
    return success_response(
        data={"case_image_id": str(image.id), "case_id": str(image.case_id)},
        message="ছবি সংযুক্ত করা হয়েছে।",
        status_code=201,
    )


@router.post(
    "/diagnosis-cases/{case_id}/analyze",
    summary="Trigger AI analysis for a diagnosis case",
)
async def analyze_case(
    case_id: UUID,
    current_user: User = Depends(require_roles("farmer", "agent")),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the AI crop disease analysis pipeline.

    The response contains:
      - AI prediction (issue, confidence, urgency)
      - Bangla advisory (if confidence is high/medium)
      - `requires_expert_review=True` if confidence is below threshold

    Safety Rule: If requires_expert_review=True, no unverified chemical
    dosages or treatment instructions are shown in the advisory.
    """
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    result = await diagnosis_service.analyze_case(db, case_id, current_user.id, user_role=user_role)
    return success_response(
        data=result.model_dump(),
        message="বিশ্লেষণ সম্পন্ন হয়েছে।",
    )


@router.get(
    "/diagnosis-cases/{case_id}",
    summary="Get the full diagnosis result for a case",
)
async def get_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch the current status, AI prediction, and advisory for a case."""
    result = await db.execute(
        select(DiagnosisCase)
        .options(
            selectinload(DiagnosisCase.predictions).selectinload(AIPrediction.details),
            selectinload(DiagnosisCase.advisory),
            selectinload(DiagnosisCase.expert_reviews),
            selectinload(DiagnosisCase.images),
        )
        .where(DiagnosisCase.id == case_id, DiagnosisCase.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message_bn": "কেসটি পাওয়া যায়নি।"},
        )

    # Ownership check: Farmers may only access their own cases; agents/admins/experts can access any
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    allowed_roles = ("admin", "administrator", "tech_admin", "technical_admin", "agent", "expert")
    if user_role not in allowed_roles and case.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message_bn": "আপনার এই কেসের তথ্য দেখার অনুমতি নেই।"},
        )

    # Build response
    advisory_data = None
    if case.advisory and getattr(case.advisory, "is_published", True):
        advisory_data = {
            "title_bn": case.advisory.title_bn,
            "summary_bn": case.advisory.summary_bn,
            "detailed_treatment_bn": case.advisory.detailed_treatment_bn,
            "preventive_measures_bn": case.advisory.preventive_measures_bn,
            "chemical_recommendations_bn": case.advisory.chemical_recommendations_bn,
            "organic_recommendations_bn": case.advisory.organic_recommendations_bn,
            "source": case.advisory.source,
        }

    latest_prediction = max(case.predictions, key=lambda p: p.created_at) if case.predictions else None
    latest_review = max(case.expert_reviews, key=lambda r: r.reviewed_at) if case.expert_reviews else None

    target_issue_id = None
    if latest_review and latest_review.verified_issue_id:
        target_issue_id = latest_review.verified_issue_id
    elif latest_prediction and latest_prediction.primary_issue_id:
        target_issue_id = latest_prediction.primary_issue_id

    issue_name_bn = None
    issue_name_en = None
    if target_issue_id:
        issue_res = await db.execute(select(Issue).where(Issue.id == target_issue_id))
        issue = issue_res.scalar_one_or_none()
        if issue:
            issue_name_bn = issue.name_bn
            issue_name_en = issue.name_en

    confidence_score = float(latest_prediction.confidence_score) if latest_prediction else None
    confidence_level = _confidence_label(confidence_score) if confidence_score is not None else None

    top_predictions = [
        {
            "rank": d.rank_order,
            "class_label": d.class_label,
            "confidence_score": float(d.confidence_score),
            "issue_id": str(d.issue_id) if d.issue_id else None,
        }
        for d in sorted(latest_prediction.details, key=lambda x: x.rank_order)
    ] if latest_prediction and latest_prediction.details else []

    images_data = [
        {
            "id": str(img.id),
            "file_id": str(img.file_id),
            "image_type": img.image_type,
            "is_primary": img.is_primary,
            "created_at": img.created_at.isoformat() if img.created_at else None,
        }
        for img in sorted(case.images, key=lambda x: (not x.is_primary, x.created_at))
    ]

    expert_reviews_data = [
        {
            "id": str(r.id),
            "expert_id": str(r.expert_id),
            "agreed_with_ai": r.agreed_with_ai,
            "verified_issue_id": str(r.verified_issue_id) if r.verified_issue_id else None,
            "diagnosis_notes_bn": r.diagnosis_notes_bn,
            "prescribed_treatment_bn": r.prescribed_treatment_bn,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
        for r in case.expert_reviews
    ]

    return success_response(
        data={
            "case_id": str(case.id),
            "case_number": case.case_number,
            "case_status": case.status,
            "status": case.status,
            "urgency_level": case.urgency_level,
            "crop_id": str(case.crop_id) if case.crop_id else None,
            "plot_id": str(case.plot_id) if case.plot_id else None,
            "farmer_notes": case.farmer_notes,
            "issue_id": str(target_issue_id) if target_issue_id else None,
            "issue_name_bn": issue_name_bn,
            "issue_name_en": issue_name_en,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "requires_expert_review": case.status == "escalated" or (latest_prediction is not None and not latest_prediction.is_confident),
            "top_predictions": top_predictions,
            "images": images_data,
            "advisory": advisory_data,
            "expert_reviews": expert_reviews_data,
            "expert_reviews_count": len(case.expert_reviews),
            "created_at": case.created_at.isoformat() if case.created_at else None,
        },
        message="কেসের তথ্য পাওয়া গেছে।",
    )


@router.delete("/diagnosis-cases/{case_id}", summary="Delete diagnosis case and trigger storage cleanup")
async def delete_diagnosis_case(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-deletes a diagnosis case and queues background garbage collection
    for any orphaned uploaded images in object storage (Supabase/S3).
    """
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    await diagnosis_service.delete_case_with_cleanup(
        db, case_id, current_user.id, user_role=user_role, background_tasks=background_tasks
    )
    await db.commit()
    return success_response(
        data={"case_id": str(case_id), "status": "deleted"},
        message="কেসটি সফলভাবে মুছে ফেলা হয়েছে এবং স্টোরেজ ক্লিনআপ শুরু হয়েছে।",
    )


@router.get("/diagnosis-cases", summary="List all diagnosis cases for the current farmer")
async def list_cases(
    limit: int = Query(50, ge=1, le=200, description="Max cases to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    **kwargs,
):
    """Returns the farmer's full case history, most recent first."""
    result = await db.execute(
        select(DiagnosisCase)
        .where(
            DiagnosisCase.farmer_id == current_user.id,
            DiagnosisCase.is_deleted == False,
        )
        .order_by(DiagnosisCase.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    cases = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(c.id),
                "case_number": c.case_number,
                "status": c.status,
                "urgency_level": c.urgency_level,
                "crop_id": str(c.crop_id) if c.crop_id else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cases
        ],
        message=f"{len(cases)}টি কেস পাওয়া গেছে।",
    )


@router.post(
    "/diagnosis-cases/{case_id}/request-expert-review",
    summary="Request a human agricultural expert to review the case",
)
async def request_expert_review(
    case_id: UUID,
    current_user: User = Depends(require_roles("farmer", "agent")),
    db: AsyncSession = Depends(get_db),
):
    """
    Farmer explicitly requests expert review (e.g., wants a second opinion).
    A CaseAssignment record is created, status history logged, and the case is escalated.
    """
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    case = await diagnosis_service.request_expert_review(db, case_id, current_user.id, user_role=user_role)

    return success_response(
        data={"case_id": str(case.id), "status": case.status},
        message="বিশেষজ্ঞ পর্যালোচনার অনুরোধ করা হয়েছে।",
    )


@router.post(
    "/diagnosis-cases/{case_id}/feedback",
    status_code=201,
    summary="Submit farmer feedback on the advisory received",
)
async def submit_feedback(
    case_id: UUID,
    payload: SubmitFeedbackRequest,
    current_user: User = Depends(require_roles("farmer", "agent")),
    db: AsyncSession = Depends(get_db),
):
    """
    Record the farmer's outcome after applying the advisory.
    Ratings (1-5 stars) and outcome status help improve advisory quality.
    """
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    feedback = await diagnosis_service.submit_feedback(db, case_id, current_user.id, payload, user_role=user_role)
    return success_response(
        data={"feedback_id": str(feedback.id)},
        message="আপনার মতামত জমা হয়েছে। ধন্যবাদ।",
        status_code=201,
    )


# ─────────────────────────────────────────────────────────
# Expert Routes
# ─────────────────────────────────────────────────────────

@expert_router.get("/cases", summary="Get the pending cases queue for agricultural experts")
async def get_expert_cases(
    limit: int = Query(50, ge=1, le=200, description="Max cases to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(require_roles("expert", "admin")),
    db: AsyncSession = Depends(get_db),
    **kwargs,
):
    """
    Returns all cases with status='escalated', prioritized by urgency.
    Experts see cases assigned to them (or unassigned if admin).
    """
    query = select(DiagnosisCase).where(
        DiagnosisCase.status == "escalated",
        DiagnosisCase.is_deleted == False,
    )
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    if user_role == "expert":
        query = query.where(
            or_(
                DiagnosisCase.assigned_expert_id == current_user.id,
                DiagnosisCase.assigned_expert_id.is_(None),
            )
        )
    query = query.order_by(
        DiagnosisCase.urgency_level.desc(),
        DiagnosisCase.created_at.asc(),
    ).limit(limit).offset(offset)
    result = await db.execute(query)
    cases = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(c.id),
                "case_number": c.case_number,
                "status": c.status,
                "urgency_level": c.urgency_level,
                "crop_id": str(c.crop_id) if c.crop_id else None,
                "farmer_notes": c.farmer_notes,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cases
        ],
        message=f"{len(cases)}টি কেস পর্যালোচনার জন্য আছে।",
    )


@expert_router.post("/cases/{case_id}/review", status_code=201, summary="Submit an expert review for a case")
async def submit_expert_review(
    case_id: UUID,
    payload: SubmitExpertReviewRequest,
    current_user: User = Depends(require_roles("expert", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Expert submits their diagnosis and treatment prescription.

    CRITICAL RULE: This creates a new record in case_mgmt.expert_reviews.
    The original AI prediction in ai.predictions is NEVER overwritten.
    Historical AI data is preserved for model evaluation and retraining.
    """
    review = await diagnosis_service.submit_expert_review(
        db, case_id, current_user.id, payload
    )
    return success_response(
        data={
            "review_id": str(review.id),
            "case_id": str(review.case_id),
            "review_status": review.review_status,
            "agreed_with_ai": review.agreed_with_ai,
        },
        message="বিশেষজ্ঞ পর্যালোচনা জমা হয়েছে।",
        status_code=201,
    )
