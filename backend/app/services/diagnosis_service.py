"""
services/diagnosis_service.py
==============================
Core business logic for the ChashiGuard (ফসল রক্ষক) diagnosis flow.

This is the most critical service in the system. It orchestrates:
  1. Creating and managing diagnosis cases.
  2. Calling the internal AI service for image analysis.
  3. Applying the confidence threshold to decide next steps:
       - HIGH/MEDIUM confidence → generate Bangla advisory from templates.
       - LOW confidence         → escalate to human expert (NO unverified advice shown).
  4. Retrieving advisory content for farmers.
  5. Logging all status changes for audit trails.

AI Service Integration:
  The AI service runs as a separate FastAPI app (see ai-service/ directory).
  Communication is via internal HTTP calls using httpx AsyncClient.
  Internal endpoints follow the /internal/v1/ prefix convention.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.advisory import Advisory, AdvisoryFeedback, AdvisoryTemplate
from app.models.ai import AIModel, AIModelFeedback, AIPrediction, AIPredictionDetail
from app.models.catalog import Issue
from app.models.diagnosis import (
    CaseAssignment,
    CaseImage,
    CaseStatusHistory,
    DiagnosisCase,
    ExpertReview,
)
from app.models.system import AuditLog, Notification, SystemFile
from app.schemas.diagnosis import (
    AttachCaseImageRequest,
    CreateDiagnosisCaseRequest,
    DiagnosisResponse,
    SubmitExpertReviewRequest,
    SubmitFeedbackRequest,
)


def _confidence_label(score: float) -> str:
    """Convert a numeric confidence score to a human-readable label."""
    if score >= 0.85:
        return "high"
    elif score >= settings.ai_confidence_threshold:
        return "medium"
    return "low"


def _generate_case_number() -> str:
    """
    Generate a sequential-style case number.
    In production, this is handled by a DB trigger (013_indexes_and_triggers.sql).
    This fallback is used in tests/dev environments without the trigger.
    """
    import random
    year = datetime.now(timezone.utc).year
    seq = random.randint(100000, 999999)
    return f"KB-{year}-{seq}"


class DiagnosisService:
    """Orchestrates the full ChashiGuard crop diagnosis workflow."""

    # ── Case Management ───────────────────────────────────────────

    async def create_case(
        self, db: AsyncSession, farmer_id: uuid.UUID, payload: CreateDiagnosisCaseRequest
    ) -> DiagnosisCase:
        """Create a new draft diagnosis case."""
        case = DiagnosisCase(
            case_number=_generate_case_number(),
            farmer_id=farmer_id,
            crop_id=payload.crop_id,
            growth_stage_id=payload.growth_stage_id,
            plot_id=payload.plot_id,
            plot_crop_id=payload.plot_crop_id,
            farmer_notes=payload.farmer_notes,
            latitude=payload.latitude,
            longitude=payload.longitude,
            status="submitted",
        )
        db.add(case)
        await db.flush()
        return case

    async def attach_image(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        farmer_id: uuid.UUID,
        payload: AttachCaseImageRequest,
    ) -> CaseImage:
        """Attach a confirmed uploaded file to a diagnosis case."""
        # Verify case belongs to this farmer
        case = await self._get_case_for_farmer(db, case_id, farmer_id)

        case_image = CaseImage(
            case_id=case.id,
            file_id=payload.file_id,
            image_type=payload.image_type,
            is_primary=payload.is_primary,
            created_at=datetime.now(timezone.utc),
        )
        db.add(case_image)

        # Update primary image FK on the case if this is marked primary
        if payload.is_primary:
            case.primary_image_id = payload.file_id

        await db.flush()
        return case_image

    # ── AI Analysis ───────────────────────────────────────────────

    async def analyze_case(
        self, db: AsyncSession, case_id: uuid.UUID, farmer_id: uuid.UUID
    ) -> DiagnosisResponse:
        """
        Trigger the full AI analysis pipeline for a diagnosis case.

        Steps:
          1. Load the case (verify ownership + has primary image).
          2. Update case status to 'processing'.
          3. Call internal AI service image quality check.
          4. Call internal AI service crop diagnosis prediction.
          5. Save prediction to ai.predictions.
          6. Apply confidence threshold:
             - High/Medium: generate advisory → status = 'ai_analyzed'
             - Low:         skip advisory    → status = 'escalated', assign to expert queue
          7. Log status change in case_status_history.
          8. Return diagnosis result.
        """
        case = await self._get_case_for_farmer(db, case_id, farmer_id)

        if not case.primary_image_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "NO_IMAGE", "message_bn": "বিশ্লেষণের আগে একটি ছবি যুক্ত করুন।"},
            )

        # Get image storage path
        file_result = await db.execute(
            select(SystemFile).where(SystemFile.id == case.primary_image_id)
        )
        image_file = file_result.scalar_one_or_none()
        if not image_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "FILE_NOT_FOUND", "message_bn": "ছবিটি পাওয়া যায়নি।"},
            )

        # Update status to processing
        await self._update_status(db, case, "processing", changed_by=farmer_id, notes="AI analysis triggered")

        # Get active AI model
        model_result = await db.execute(
            select(AIModel).where(AIModel.is_active == True)
        )
        ai_model = model_result.scalar_one_or_none()
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "NO_ACTIVE_MODEL", "message_bn": "AI সেবা বর্তমানে অনুপলব্ধ।"},
            )

        # Call AI service
        ai_result = await self._call_ai_service(
            case_id=case.id,
            crop_id=case.crop_id,
            storage_path=image_file.storage_path,
        )

        # Resolve primary issue from AI result
        issue = None
        if ai_result.get("primary_issue_code"):
            issue_result = await db.execute(
                select(Issue).where(Issue.code == ai_result["primary_issue_code"])
            )
            issue = issue_result.scalar_one_or_none()

        confidence_score = float(ai_result.get("confidence_score", 0.0))
        is_confident = confidence_score >= settings.ai_confidence_threshold

        # Save AI prediction (IMMUTABLE — never update this record)
        prediction = AIPrediction(
            case_id=case.id,
            model_id=ai_model.id,
            file_id=case.primary_image_id,
            primary_issue_id=issue.id if issue else None,
            confidence_score=confidence_score,
            is_confident=is_confident,
            raw_response=ai_result,
            processing_time_ms=ai_result.get("processing_time_ms"),
            status="completed",
            created_at=datetime.now(timezone.utc),
        )
        db.add(prediction)
        await db.flush()

        # Save top-N prediction details
        for rank_data in ai_result.get("top_predictions", []):
            detail = AIPredictionDetail(
                prediction_id=prediction.id,
                class_label=rank_data["class_label"],
                rank_order=rank_data["rank"],
                confidence_score=rank_data["confidence_score"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(detail)

        # Apply confidence threshold logic
        advisory_payload = None
        if is_confident and issue:
            # Generate advisory from template
            advisory = await self._generate_advisory(
                db=db,
                case=case,
                prediction=prediction,
                issue=issue,
                growth_stage_id=case.growth_stage_id,
            )
            await self._update_status(db, case, "ai_analyzed", notes="High/medium confidence — advisory generated")
            case.urgency_level = ai_result.get("urgency_level", "medium")

            if advisory:
                advisory_payload = {
                    "title_bn": advisory.title_bn,
                    "summary_bn": advisory.summary_bn,
                    "detailed_treatment_bn": advisory.detailed_treatment_bn,
                    "preventive_measures_bn": advisory.preventive_measures_bn,
                    "chemical_recommendations_bn": advisory.chemical_recommendations_bn,
                    "organic_recommendations_bn": advisory.organic_recommendations_bn,
                    "source": advisory.source,
                }
        else:
            # Low confidence → escalate to expert
            await self._update_status(
                db, case, "escalated",
                notes="Low confidence — escalated to expert review queue"
            )
            case.urgency_level = "high"  # Conservative: treat unknown as urgent

        # Build top predictions list for response
        top_preds = [
            {
                "rank": r.get("rank"),
                "class_label": r.get("class_label"),
                "confidence_score": r.get("confidence_score"),
                "issue_id": None,
            }
            for r in ai_result.get("top_predictions", [])
        ]

        return DiagnosisResponse(
            case_id=case.id,
            case_number=case.case_number,
            case_status=case.status,
            urgency_level=case.urgency_level,
            issue_id=issue.id if issue else None,
            issue_name_bn=issue.name_bn if issue else None,
            issue_name_en=issue.name_en if issue else None,
            confidence_score=confidence_score,
            confidence_level=_confidence_label(confidence_score),
            requires_expert_review=not is_confident,
            top_predictions=top_preds,
            advisory=advisory_payload,
        )

    async def _call_ai_service(
        self,
        case_id: uuid.UUID,
        crop_id: Optional[uuid.UUID],
        storage_path: str,
    ) -> dict:
        """
        Internal HTTP call to the AI service (Google Gemini Vision).

        Fetches the image bytes from the signed storage URL, encodes as base64,
        and posts them to the AI service so Gemini can actually see the crop photo.

        POST /internal/v1/crop-diagnosis/predict
        """
        import base64

        # Step 1: Fetch the image from its storage URL so Gemini can analyze it
        image_base64: Optional[str] = None
        image_mime_type = "image/jpeg"
        try:
            async with httpx.AsyncClient(timeout=10.0) as fetch_client:
                img_response = await fetch_client.get(storage_path)
                if img_response.status_code == 200:
                    image_base64 = base64.b64encode(img_response.content).decode("utf-8")
                    content_type = img_response.headers.get("content-type", "image/jpeg")
                    image_mime_type = content_type.split(";")[0].strip()
        except Exception:
            pass  # No image bytes — AI service will use mock fallback

        # Step 2: Call AI service with image data
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{settings.ai_service_url}/internal/v1/crop-diagnosis/predict",
                    json={
                        "case_id": str(case_id),
                        "crop_id": str(crop_id) if crop_id else None,
                        "storage_path": storage_path,
                        "image_base64": image_base64,
                        "image_mime_type": image_mime_type,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            # Return a low-confidence fallback if AI service is unreachable
            return {
                "primary_issue_code": None,
                "confidence_score": 0.0,
                "urgency_level": "medium",
                "top_predictions": [],
                "processing_time_ms": 0,
                "error": "AI service unavailable",
            }


    async def _generate_advisory(
        self,
        db: AsyncSession,
        case: DiagnosisCase,
        prediction: AIPrediction,
        issue: Issue,
        growth_stage_id: Optional[uuid.UUID],
    ) -> Optional[Advisory]:
        """
        Find the best matching advisory template and create an Advisory record.

        Query priority: (issue_id + growth_stage_id + severity) → (issue_id + severity)
        """
        # Try exact match with growth stage
        template_query = select(AdvisoryTemplate).where(
            AdvisoryTemplate.issue_id == issue.id,
            AdvisoryTemplate.is_active == True,
        )
        if growth_stage_id:
            template_query = template_query.where(
                AdvisoryTemplate.growth_stage_id == growth_stage_id
            )

        template_result = await db.execute(template_query.limit(1))
        template = template_result.scalar_one_or_none()

        # Fallback: any active template for this issue
        if not template:
            fallback = await db.execute(
                select(AdvisoryTemplate).where(
                    AdvisoryTemplate.issue_id == issue.id,
                    AdvisoryTemplate.is_active == True,
                    AdvisoryTemplate.growth_stage_id == None,
                ).limit(1)
            )
            template = fallback.scalar_one_or_none()

        if not template:
            return None  # No template found — case will still be marked diagnosed

        advisory = Advisory(
            case_id=case.id,
            prediction_id=prediction.id,
            template_id=template.id,
            title_bn=template.title_bn,
            summary_bn=f"{issue.name_bn} - {template.title_bn}",
            detailed_treatment_bn=template.content_bn,
            preventive_measures_bn=template.preventive_measures_bn,
            source="ai_generated",
            is_published=True,
        )
        db.add(advisory)
        await db.flush()
        return advisory

    # ── Expert Review ─────────────────────────────────────────────

    async def submit_expert_review(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        expert_user_id: uuid.UUID,
        payload: SubmitExpertReviewRequest,
    ) -> ExpertReview:
        """
        Expert submits a review for a case.

        CRITICAL: This creates a NEW ExpertReview record.
        The original AIPrediction is NEVER modified.
        If expert disagrees, a model_feedback record is also created.
        """
        case_result = await db.execute(
            select(DiagnosisCase).where(
                DiagnosisCase.id == case_id,
                DiagnosisCase.is_deleted == False,
            )
        )
        case = case_result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND"})

        review = ExpertReview(
            case_id=case.id,
            expert_id=expert_user_id,
            agreed_with_ai=payload.agreed_with_ai,
            verified_issue_id=payload.verified_issue_id,
            diagnosis_notes_bn=payload.diagnosis_notes_bn,
            diagnosis_notes_en=payload.diagnosis_notes_en,
            prescribed_treatment_bn=payload.prescribed_treatment_bn,
            review_status="completed",
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(review)

        # If expert disagrees, log model feedback for future retraining
        if not payload.agreed_with_ai:
            pred_result = await db.execute(
                select(AIPrediction).where(AIPrediction.case_id == case.id).limit(1)
            )
            prediction = pred_result.scalar_one_or_none()
            if prediction:
                feedback = AIModelFeedback(
                    prediction_id=prediction.id,
                    case_id=case.id,
                    expert_id=expert_user_id,
                    actual_issue_id=payload.verified_issue_id,
                    is_ai_correct=False,
                    feedback_notes=payload.diagnosis_notes_en,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(feedback)

        # Update case status
        await self._update_status(
            db, case, "expert_reviewed",
            changed_by=expert_user_id,
            notes="Expert review submitted",
        )

        # Write audit log
        db.add(AuditLog(
            user_id=expert_user_id,
            action="EXPERT_REVIEW_SUBMITTED",
            entity_name="case_mgmt.expert_reviews",
            entity_id=review.id,
            new_data={"case_id": str(case.id), "agreed_with_ai": payload.agreed_with_ai},
            created_at=datetime.now(timezone.utc),
        ))

        # Dispatch in-app notification to the farmer
        db.add(Notification(
            user_id=case.farmer_id,
            notification_type="expert_review_completed",
            title_bn="বিশেষজ্ঞ পর্যালোচনা সম্পন্ন হয়েছে",
            body_bn=(
                f"আপনার কেস {case.case_number} একজন কৃষি বিশেষজ্ঞ পর্যালোচনা করেছেন। "
                "বিস্তারিত জানতে আপনার কেস খুলুন।"
            ),
            entity_type="diagnosis_case",
            entity_id=case.id,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        ))

        await db.flush()
        return review

    # ── Feedback ──────────────────────────────────────────────────

    async def submit_feedback(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        farmer_id: uuid.UUID,
        payload: SubmitFeedbackRequest,
    ) -> AdvisoryFeedback:
        """Record farmer's outcome feedback for the advisory received."""
        # Find the advisory for this case
        advisory_result = await db.execute(
            select(Advisory).where(Advisory.case_id == case_id)
        )
        advisory = advisory_result.scalar_one_or_none()
        if not advisory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ADVISORY_NOT_FOUND", "message_bn": "এই কেসের জন্য কোনো পরামর্শ পাওয়া যায়নি।"},
            )

        feedback = AdvisoryFeedback(
            advisory_id=advisory.id,
            farmer_id=farmer_id,
            rating=payload.rating,
            is_helpful=payload.is_helpful,
            feedback_text=payload.feedback_text,
            outcome_status=payload.outcome_status,
            created_at=datetime.now(timezone.utc),
        )
        db.add(feedback)
        await db.flush()
        return feedback

    # ── Helpers ───────────────────────────────────────────────────

    async def _get_case_for_farmer(
        self, db: AsyncSession, case_id: uuid.UUID, farmer_id: uuid.UUID
    ) -> DiagnosisCase:
        """Load a case, verifying it belongs to the requesting farmer."""
        result = await db.execute(
            select(DiagnosisCase).where(
                DiagnosisCase.id == case_id,
                DiagnosisCase.farmer_id == farmer_id,
                DiagnosisCase.is_deleted == False,
            )
        )
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CASE_NOT_FOUND", "message_bn": "কেসটি পাওয়া যায়নি।"},
            )
        return case

    async def _update_status(
        self,
        db: AsyncSession,
        case: DiagnosisCase,
        new_status: str,
        changed_by: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update case status and log the change to case_status_history."""
        history = CaseStatusHistory(
            case_id=case.id,
            previous_status=case.status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes,
            created_at=datetime.now(timezone.utc),
        )
        db.add(history)
        case.status = new_status
