"""
services/diagnosis_service.py
==============================
Core business logic for the ChashiGuard diagnosis flow.

It orchestrates:
  1. Creating and managing diagnosis cases.
  2. Calling the internal AI service for image analysis.
  3. Applying the confidence threshold to decide next steps:
       - HIGH/MEDIUM confidence -> generate Bangla advisory from templates.
       - LOW confidence         -> escalate to human expert.
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
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.advisory import Advisory, AdvisoryFeedback, AdvisoryTemplate
from app.models.ai import AIModel, AIModelFeedback, AIPrediction, AIPredictionDetail
from app.models.auth import User
from app.models.catalog import Crop, GrowthStage, Issue, Remedy
from app.models.farm import Plot, PlotCrop
from app.models.diagnosis import (
    CaseAssignment,
    CaseImage,
    CaseStatusHistory,
    DiagnosisCase,
    ExpertProfile,
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
from app.services.storage_service import storage_service


def _confidence_label(score: float) -> str:
    """Convert a numeric confidence score to a human-readable label."""
    if score >= 0.85:
        return "high"
    elif score >= settings.ai_confidence_threshold:
        return "medium"
    return "low"


def _normalize_code(value: Optional[str]) -> str:
    """Normalize an issue code or label: 'Potato Late Blight' -> 'potato_late_blight'."""
    if not value:
        return ""
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _pred_code(item: dict) -> str:
    """Best-effort issue code for one top_predictions item."""
    return _normalize_code(
        item.get("issue_code") or item.get("class_label") or item.get("class")
    )


async def _generate_case_number(db: AsyncSession) -> str:
    """
    Generate a sequential, human-readable case number (e.g., KB-2026-000124).
    Uses the PostgreSQL sequence case_mgmt.case_number_seq, falling back to
    table count or random hex if running without sequences.
    """
    year = datetime.now(timezone.utc).year
    try:
        res = await db.execute(text("SELECT nextval('case_mgmt.case_number_seq')"))
        seq = res.scalar()
        if seq:
            return f"KB-{year}-{seq:06d}"
    except Exception:
        pass

    try:
        res = await db.execute(select(func.count(DiagnosisCase.id)))
        count = (res.scalar() or 0) + 1
        return f"KB-{year}-{count:06d}"
    except Exception:
        suffix = uuid.uuid4().hex[:6].upper()
        return f"KB-{year}-{suffix}"


class DiagnosisService:
    """Orchestrates the full ChashiGuard crop diagnosis workflow."""

    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        # Timeouts are passed per request, so the shared client has a generous default.
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=90.0)
        return self._http_client

    async def close(self) -> None:
        """Close shared HTTP client on shutdown."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    # -- Case Management ---------------------------------------------------

    async def create_case(
        self,
        db: AsyncSession,
        farmer_id: uuid.UUID,
        payload: CreateDiagnosisCaseRequest,
        user_role: str = "farmer",
        **kwargs,
    ) -> DiagnosisCase:
        """Create a new draft diagnosis case with cross-entity IDOR checks."""
        # 0. Validate crop exists
        crop_res = await db.execute(
            select(Crop.id).where(Crop.id == payload.crop_id)
        )
        if crop_res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CROP_NOT_FOUND", "message_bn": "ফসলটি পাওয়া যায়নি।"},
            )

        # 1. Validate plot_id belongs to the farmer
        if payload.plot_id:
            plot_res = await db.execute(
                select(Plot).where(
                    Plot.id == payload.plot_id,
                    Plot.user_id == farmer_id,
                    Plot.is_deleted == False,
                )
            )
            plot = plot_res.scalar_one_or_none()
            if not plot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "PLOT_NOT_FOUND", "message_bn": "নির্দিষ্ট জমিটি পাওয়া যায়নি বা এই জমিটি আপনার নয়।"},
                )

        # 2. Validate plot_crop_id matches plot and crop and belongs to farmer
        if payload.plot_crop_id:
            plot_crop_res = await db.execute(
                select(PlotCrop).where(
                    PlotCrop.id == payload.plot_crop_id,
                    PlotCrop.is_deleted == False,
                )
            )
            plot_crop = plot_crop_res.scalar_one_or_none()
            if not plot_crop:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "PLOT_CROP_NOT_FOUND", "message_bn": "ফসলের চক্রটি পাওয়া যায়নি।"},
                )
            # Ensure plot belongs to the farmer
            crop_plot = await db.get(Plot, plot_crop.plot_id)
            if not crop_plot or crop_plot.is_deleted or crop_plot.user_id != farmer_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message_bn": "অন্য কৃষকের জমির ফসল চক্র ব্যবহারের অনুমতি নেই।"},
                )
            if (payload.plot_id and plot_crop.plot_id != payload.plot_id) or (plot_crop.crop_id != payload.crop_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_PLOT_CROP", "message_bn": "ফসলের চক্রটি নির্বাচিত জমি বা ফসলের সাথে মেলে না।"},
                )

        # 3. Validate growth_stage_id belongs to crop_id
        if payload.growth_stage_id:
            stage_res = await db.execute(
                select(GrowthStage).where(
                    GrowthStage.id == payload.growth_stage_id,
                )
            )
            stage = stage_res.scalar_one_or_none()
            if not stage or stage.crop_id != payload.crop_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_GROWTH_STAGE", "message_bn": "নির্বাচিত বৃদ্ধির পর্যায়টি এই ফসলের জন্য প্রযোজ্য নয়।"},
                )

        case_num = await _generate_case_number(db)
        case = DiagnosisCase(
            case_number=case_num,
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
        db.add(
            AuditLog(
                user_id=farmer_id,
                action="DIAGNOSIS_SUBMITTED",
                entity_name="case_mgmt.diagnosis_cases",
                entity_id=case.id,
                new_data={"case_id": str(case.id), "case_number": case.case_number},
                created_at=datetime.now(timezone.utc),
            )
        )
        await db.flush()
        return case

    async def attach_image(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        farmer_id: uuid.UUID,
        payload: AttachCaseImageRequest,
        user_role: str = "farmer",
        **kwargs,
    ) -> CaseImage:
        """Attach a confirmed uploaded file to a diagnosis case."""
        # Verify case belongs to this farmer (or user is agent/admin)
        case = await self._get_case_for_farmer(db, case_id, farmer_id, user_role=user_role)

        # Verify file exists and belongs to this user, the case farmer, or privileged role
        file_result = await db.execute(
            select(SystemFile).where(
                SystemFile.id == payload.file_id,
                SystemFile.is_deleted == False,
            )
        )
        file_record = file_result.scalar_one_or_none()
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "FILE_NOT_FOUND", "message_bn": "ফাইলটি পাওয়া যায়নি।"},
            )
        allowed_roles = ("agent", "admin", "administrator", "tech_admin", "technical_admin")
        if file_record.uploaded_by != farmer_id and file_record.uploaded_by != case.farmer_id and user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message_bn": "অন্য ব্যবহারকারীর ফাইল যুক্ত করার অনুমতি নেই।"},
            )

        # Check if file is already attached to another case
        already_attached = await db.execute(
            select(CaseImage).where(
                CaseImage.file_id == payload.file_id,
                CaseImage.case_id != case.id,
            )
        )
        if already_attached.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "FILE_ALREADY_ATTACHED", "message_bn": "এই ফাইলটি ইতিমধ্যে অন্য একটি কেসে যুক্ত করা হয়েছে।"},
            )

        # Gatekeeper image validation: verify attached image is a valid crop
        if file_record and getattr(file_record, "mime_type", None) and file_record.mime_type.startswith("image/"):
            file_bytes = await storage_service.get_file_bytes(file_record.storage_path)
            if file_bytes:
                from app.services.image_gatekeeper import (
                    verify_crop_image_gatekeeper,
                    get_system_available_crops,
                    get_gemini_client,
                )
                avail_crops = await get_system_available_crops(db)
                crop_code = "potato"
                if case.crop_id:
                    crop_row = await db.execute(select(Crop).where(Crop.id == case.crop_id))
                    c_obj = crop_row.scalar_one_or_none()
                    if c_obj:
                        crop_code = c_obj.code
                verification = await verify_crop_image_gatekeeper(
                    gemini_client=get_gemini_client(),
                    image_bytes=file_bytes,
                    mime_type=file_record.mime_type,
                    selected_crop=crop_code,
                    available_crops=avail_crops,
                )
                if not verification.is_crop or verification.action_status == "REJECT_NOT_CROP":
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={"code": "REJECT_NOT_CROP", "message_bn": verification.message_bn},
                    )

        # If this image is primary, reset any previous primary images for this case
        if payload.is_primary:
            await db.execute(
                update(CaseImage)
                .where(CaseImage.case_id == case.id)
                .values(is_primary=False)
            )
            case.primary_image_id = payload.file_id

        case_image = CaseImage(
            case_id=case.id,
            file_id=payload.file_id,
            image_type=payload.image_type,
            is_primary=payload.is_primary,
            created_at=datetime.now(timezone.utc),
        )
        db.add(case_image)

        await db.flush()
        return case_image

    # -- AI Analysis -------------------------------------------------------

    async def analyze_case(
        self, db: AsyncSession, case_id: uuid.UUID, farmer_id: uuid.UUID, user_role: str = "farmer", **kwargs
    ) -> DiagnosisResponse:
        """
        Trigger the full AI analysis pipeline for a diagnosis case.

        Steps:
          1. Load the case (verify ownership + has primary image).
          2. Update case status to 'processing'.
          3. Call internal AI service crop diagnosis prediction.
          4. Save prediction to ai.predictions.
          5. Apply confidence threshold:
             - High/Medium: generate advisory -> status = 'ai_analyzed'
             - Low:         skip advisory    -> status = 'escalated', assign to expert queue
          6. Log status change in case_status_history.
          7. Return diagnosis result.
        """
        case = await self._get_case_for_farmer(db, case_id, farmer_id, user_role=user_role)

        # Prevent duplicate analysis on completed cases
        if case.status in ("ai_analyzed", "expert_reviewed", "closed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CASE_ALREADY_ANALYZED",
                    "message_bn": "এই কেসটি ইতিমধ্যে বিশ্লেষণ করা হয়েছে। পুনরায় বিশ্লেষণের প্রয়োজন নেই।",
                },
            )

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

        # Get active AI model BEFORE committing
        model_result = await db.execute(
            select(AIModel)
            .where(AIModel.is_active == True)
            .order_by(AIModel.created_at.desc())
            .limit(1)
        )
        ai_model = model_result.scalar_one_or_none()
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "NO_ACTIVE_MODEL", "message_bn": "AI সেবা বর্তমানে অনুপলব্ধ।"},
            )

        # Update status to processing and commit to release DB connection during external AI call
        await self._update_status(db, case, "processing", changed_by=farmer_id, notes="AI analysis triggered")
        await db.commit()

        try:
            # Call AI service (executed with NO active DB transaction)
            ai_result = await self._call_ai_service(
                case_id=case.id,
                crop_id=case.crop_id,
                storage_path=image_file.storage_path,
            )

            # Resolve primary issue from AI result (case-insensitive match)
            issue = None
            primary_code = _normalize_code(ai_result.get("primary_issue_code"))
            if primary_code:
                issue_result = await db.execute(
                    select(Issue).where(func.lower(Issue.code) == primary_code)
                )
                issue = issue_result.scalar_one_or_none()

            confidence_score = float(ai_result.get("confidence_score", 0.0))
            is_confident = confidence_score >= settings.ai_confidence_threshold

            # Save AI prediction (IMMUTABLE - never update this record)
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
            db.add(
                AuditLog(
                    user_id=farmer_id,
                    action="AI_PREDICTION_MADE",
                    entity_name="ai.predictions",
                    entity_id=prediction.id,
                    new_data={"case_id": str(case.id), "confidence_score": float(confidence_score), "is_confident": is_confident},
                    created_at=datetime.now(timezone.utc),
                )
            )
            await db.flush()

            # Resolve issue_ids for top_predictions (Bug 3.1)
            top_predictions = ai_result.get("top_predictions", []) or []
            top_codes = [c for c in (_pred_code(r) for r in top_predictions) if c]
            issue_map = {}
            if top_codes:
                issues_res = await db.execute(
                    select(Issue).where(func.lower(Issue.code).in_(top_codes))
                )
                for iss in issues_res.scalars().all():
                    issue_map[iss.code.lower()] = iss.id

            # Save top-N prediction details with matched issue_id
            resolved_ids = []
            for idx, rank_data in enumerate(top_predictions):
                label = rank_data.get("class_label") or rank_data.get("class")
                matched_id = issue_map.get(_pred_code(rank_data))
                if matched_id is None and idx == 0 and issue:
                    matched_id = issue.id  # rank 1 is the primary issue
                resolved_ids.append(matched_id)
                rank = rank_data.get("rank") or rank_data.get("rank_order") or (idx + 1)
                conf = rank_data.get("confidence_score") or rank_data.get("confidence") or 0.0
                detail = AIPredictionDetail(
                    prediction_id=prediction.id,
                    issue_id=matched_id,
                    class_label=label,
                    rank_order=rank,
                    confidence_score=conf,
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
                await self._update_status(db, case, "ai_analyzed", notes="High/medium confidence - advisory generated")
                case.urgency_level = ai_result.get("urgency_level", "medium")
                case.resolved_at = datetime.now(timezone.utc)

                if advisory:
                    db.add(
                        AuditLog(
                            user_id=farmer_id,
                            action="ADVISORY_PUBLISHED",
                            entity_name="advisories",
                            entity_id=advisory.id,
                            new_data={"case_id": str(case.id), "title_bn": advisory.title_bn},
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                    db.add(
                        Notification(
                            user_id=case.farmer_id,
                            notification_type="case_status_changed",
                            title_bn="কেস বিশ্লেষণ সম্পন্ন",
                            body_bn="আপনার ফসলের রোগ নির্ণয় সফলভাবে সম্পন্ন হয়েছে এবং পরামর্শ প্রদান করা হয়েছে।",
                            entity_type="diagnosis_case",
                            entity_id=case.id,
                            created_at=datetime.now(timezone.utc),
                        )
                    )
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
                # Low confidence (or unknown issue) -> escalate to expert
                # Unpublish any previously generated advisory to prevent stale advice
                existing_adv_res = await db.execute(
                    select(Advisory).where(Advisory.case_id == case.id)
                )
                existing_adv = existing_adv_res.scalar_one_or_none()
                if existing_adv:
                    existing_adv.is_published = False

                await self._update_status(
                    db, case, "escalated",
                    notes="Low confidence - escalated to expert review queue"
                )
                case.urgency_level = "high"  # Conservative: treat unknown as urgent

                # Auto-assign available expert if not yet assigned
                if not case.assigned_expert_id:
                    expert_query = (
                        select(ExpertProfile)
                        .where(ExpertProfile.is_available == True)
                        .order_by(ExpertProfile.rating.desc())
                        .limit(1)
                    )
                    expert_result = await db.execute(expert_query)
                    expert_profile = expert_result.scalar_one_or_none()
                    if expert_profile and hasattr(expert_profile, "user_id") and isinstance(expert_profile, ExpertProfile):
                        case.assigned_expert_id = expert_profile.user_id
                        assignment = CaseAssignment(
                            case_id=case.id,
                            expert_id=expert_profile.user_id,
                            assigned_by=farmer_id,
                            status="assigned",
                            assigned_at=datetime.now(timezone.utc),
                        )
                        db.add(assignment)
                        db.add(
                            Notification(
                                user_id=expert_profile.user_id,
                                notification_type="case_assigned",
                                title_bn="নতুন কেস বরাদ্দ",
                                body_bn=f"কেস {case.case_number} আপনার পর্যালোচনার জন্য বরাদ্দ করা হয়েছে।",
                                entity_type="diagnosis_case",
                                entity_id=case.id,
                                created_at=datetime.now(timezone.utc),
                            )
                        )

                db.add(
                    Notification(
                        user_id=case.farmer_id,
                        notification_type="case_status_changed",
                        title_bn="কেস বিশেষজ্ঞের কাছে পাঠানো হয়েছে",
                        body_bn=f"কেস {case.case_number} বিশেষজ্ঞের পর্যালোচনার জন্য পাঠানো হয়েছে।",
                        entity_type="diagnosis_case",
                        entity_id=case.id,
                        created_at=datetime.now(timezone.utc),
                    )
                )

            # Build top predictions list for response
            top_preds = [
                {
                    "rank": r.get("rank") or r.get("rank_order") or (i + 1),
                    "class_label": r.get("class_label") or r.get("class"),
                    "confidence_score": r.get("confidence_score") or r.get("confidence") or 0.0,
                    "issue_id": str(resolved_ids[i]) if resolved_ids[i] else None,
                }
                for i, r in enumerate(top_predictions)
            ]

            # Explicitly commit all analysis results, predictions, and advisories to the DB
            await db.commit()
        except HTTPException:
            if db.in_transaction():
                await db.rollback()
            case.status = "submitted"
            try:
                case_refresh = await db.get(DiagnosisCase, case.id)
                if case_refresh:
                    case_refresh.status = "submitted"
                    await db.commit()
            except Exception:
                pass
            raise
        except Exception as e:
            # Reset case status to submitted so it does not get stuck in processing
            if db.in_transaction():
                await db.rollback()
            case.status = "submitted"
            try:
                case_refresh = await db.get(DiagnosisCase, case.id)
                if case_refresh:
                    case_refresh.status = "submitted"
                    await db.commit()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_ANALYSIS_FAILED", "message_bn": "AI বিশ্লেষণ ব্যর্থ হয়েছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"}
            ) from e

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
            if storage_path.startswith("http://") or storage_path.startswith("https://"):
                signed_url = storage_path
            else:
                signed_url = storage_service.generate_view_url(storage_path)

            fetch_client = self._get_client()
            img_response = await fetch_client.get(signed_url, timeout=10.0)
            if img_response.status_code == 200:
                image_base64 = base64.b64encode(img_response.content).decode("utf-8")
                content_type = img_response.headers.get("content-type", "image/jpeg")
                image_mime_type = content_type.split(";")[0].strip()
        except Exception:
            pass  # No image bytes - AI service will use mock fallback

        # Step 2: Call AI service with image data
        try:
            client = self._get_client()
            response = await client.post(
                f"{settings.ai_service_url}/internal/v1/crop-diagnosis/predict",
                json={
                    "case_id": str(case_id),
                    "crop_id": str(crop_id) if crop_id else None,
                    "storage_path": storage_path,
                    "image_base64": image_base64,
                    "image_mime_type": image_mime_type,
                },
                timeout=90.0,
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

        Query priority: (issue_id + growth_stage_id) -> (issue_id, any stage)
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
            return None  # No template found - case will still be marked diagnosed

        # Query active remedies for this issue from catalog.remedies (Bug 1.2)
        remedies_res = await db.execute(
            select(Remedy).where(
                Remedy.issue_id == issue.id,
                Remedy.is_active == True,
            )
        )
        remedies = remedies_res.scalars().all()

        chem_recs = []
        org_recs = []
        for rem in remedies:
            desc = rem.title_bn
            if rem.dosage_bn:
                desc += f" (মাত্রা: {rem.dosage_bn})"
            if rem.description_bn and rem.description_bn != rem.title_bn:
                desc += f" - {rem.description_bn}"

            if rem.type == "chemical":
                chem_recs.append(desc)
            elif rem.type in ("organic", "cultural"):
                org_recs.append(desc)

        chemical_recs_str = "\n".join(chem_recs) if chem_recs else None
        organic_recs_str = "\n".join(org_recs) if org_recs else None

        # Check if an advisory already exists for this case to prevent UniqueViolationError
        existing_adv_result = await db.execute(
            select(Advisory).where(Advisory.case_id == case.id)
        )
        existing_advisory = existing_adv_result.scalar_one_or_none()
        if existing_advisory:
            existing_advisory.prediction_id = prediction.id
            existing_advisory.template_id = template.id
            existing_advisory.title_bn = template.title_bn
            existing_advisory.summary_bn = f"{issue.name_bn} - {template.title_bn}"
            existing_advisory.detailed_treatment_bn = template.content_bn
            existing_advisory.preventive_measures_bn = template.preventive_measures_bn
            existing_advisory.chemical_recommendations_bn = chemical_recs_str
            existing_advisory.organic_recommendations_bn = organic_recs_str
            existing_advisory.source = "ai_generated"
            existing_advisory.is_published = True
            await db.flush()
            return existing_advisory

        advisory = Advisory(
            case_id=case.id,
            prediction_id=prediction.id,
            template_id=template.id,
            title_bn=template.title_bn,
            summary_bn=f"{issue.name_bn} - {template.title_bn}",
            detailed_treatment_bn=template.content_bn,
            preventive_measures_bn=template.preventive_measures_bn,
            chemical_recommendations_bn=chemical_recs_str,
            organic_recommendations_bn=organic_recs_str,
            source="ai_generated",
            is_published=True,
        )
        db.add(advisory)
        await db.flush()
        return advisory

    # -- Expert Review -----------------------------------------------------

    async def submit_expert_review(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        expert_user_id: Optional[uuid.UUID] = None,
        payload: Optional[SubmitExpertReviewRequest] = None,
        expert_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> ExpertReview:
        """
        Expert submits a review for a case.

        CRITICAL: This creates a NEW ExpertReview record.
        The original AIPrediction is NEVER modified.
        If expert disagrees, a model_feedback record is also created.
        """
        expert_user_id = expert_user_id or expert_id
        if not expert_user_id or not payload:
            raise HTTPException(status_code=400, detail={"code": "INVALID_ARGUMENTS"})

        case_result = await db.execute(
            select(DiagnosisCase).where(
                DiagnosisCase.id == case_id,
                DiagnosisCase.is_deleted == False,
            )
        )
        case = case_result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND"})

        if case.status in ("closed", "expert_reviewed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CASE_ALREADY_REVIEWED", "message_bn": "এই কেসটি ইতিমধ্যে পর্যালোচনা বা সমাপ্ত করা হয়েছে।"},
            )

        if case.assigned_expert_id and case.assigned_expert_id != expert_user_id:
            user_res = await db.execute(
                select(User).options(selectinload(User.role)).where(User.id == expert_user_id)
            )
            u = user_res.scalar_one_or_none()
            role = u.role_code if u and hasattr(u, "role_code") else (u.role.code if u and u.role else "")
            if role not in ("admin", "administrator", "tech_admin", "technical_admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message_bn": "এই কেসটি অন্য একজন বিশেষজ্ঞের দায়িত্বে রয়েছে।"},
                )

        if not case.assigned_expert_id:
            case.assigned_expert_id = expert_user_id

        # Set resolved_at timestamp
        case.resolved_at = datetime.now(timezone.utc)

        # Determine verified_issue_id
        verified_issue_id = payload.verified_issue_id
        if payload.agreed_with_ai and not verified_issue_id:
            pred_res = await db.execute(
                select(AIPrediction)
                .where(AIPrediction.case_id == case.id)
                .order_by(AIPrediction.created_at.desc())
                .limit(1)
            )
            latest_pred = pred_res.scalar_one_or_none()
            if latest_pred and latest_pred.primary_issue_id:
                verified_issue_id = latest_pred.primary_issue_id

        # Validate verified_issue_id exists in catalog.issues
        if verified_issue_id:
            issue_res = await db.execute(
                select(Issue).where(
                    Issue.id == verified_issue_id,
                    Issue.is_active == True,
                )
            )
            issue_record = issue_res.scalar_one_or_none()
            if not issue_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "ISSUE_NOT_FOUND", "message_bn": "নির্দিষ্ট রোগটি পাওয়া যায়নি বা সক্রিয় নয়।"},
                )

        review = ExpertReview(
            case_id=case.id,
            expert_id=expert_user_id,
            agreed_with_ai=payload.agreed_with_ai,
            verified_issue_id=verified_issue_id,
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
                select(AIPrediction).where(AIPrediction.case_id == case.id).order_by(AIPrediction.created_at.desc()).limit(1)
            )
            prediction = pred_result.scalar_one_or_none()
            if prediction:
                feedback = AIModelFeedback(
                    prediction_id=prediction.id,
                    case_id=case.id,
                    expert_id=expert_user_id,
                    actual_issue_id=verified_issue_id,
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

        # Update case_mgmt.case_assignments table (Bug 1.2)
        now_utc = datetime.now(timezone.utc)
        assign_result = await db.execute(
            select(CaseAssignment).where(
                CaseAssignment.case_id == case.id,
                CaseAssignment.expert_id == expert_user_id,
            )
        )
        assignments = assign_result.scalars().all()
        for assignment in assignments:
            assignment.status = "completed"
            assignment.responded_at = now_utc

        if not assignments:
            db.add(CaseAssignment(
                case_id=case.id,
                expert_id=expert_user_id,
                assigned_by=expert_user_id,
                status="completed",
                assigned_at=now_utc,
                responded_at=now_utc,
            ))

        # Write audit log
        db.add(AuditLog(
            user_id=expert_user_id,
            action="EXPERT_REVIEW_SUBMITTED",
            entity_name="case_mgmt.expert_reviews",
            entity_id=review.id,
            new_data={"case_id": str(case.id), "agreed_with_ai": payload.agreed_with_ai},
            created_at=datetime.now(timezone.utc),
        ))

        # Update or create Advisory record with expert diagnosis and treatment
        advisory_result = await db.execute(
            select(Advisory).where(Advisory.case_id == case.id)
        )
        advisory = advisory_result.scalar_one_or_none()
        source = "expert_approved" if payload.agreed_with_ai else "expert_overridden"
        title = payload.diagnosis_notes_bn[:100] if payload.diagnosis_notes_bn else "বিশেষজ্ঞ পর্যালোচনা পরামর্শ"
        if not title.startswith("বিশেষজ্ঞ"):
            title = f"বিশেষজ্ঞ পরামর্শ: {title}"

        treatment_bn = payload.prescribed_treatment_bn or payload.diagnosis_notes_bn or "বিশেষজ্ঞ পরামর্শ দেওয়া হয়েছে।"
        summary_bn = payload.diagnosis_notes_bn or "বিশেষজ্ঞ কর্তৃক পর্যালোচিত পরামর্শ।"

        if advisory:
            advisory.source = source
            advisory.created_by = expert_user_id
            advisory.detailed_treatment_bn = treatment_bn
            advisory.summary_bn = summary_bn
            advisory.title_bn = title
            advisory.is_published = True

            db.add(Notification(
                user_id=case.farmer_id,
                notification_type="advisory_updated",
                title_bn="পরামর্শ আপডেট হয়েছে",
                body_bn=f"কেস {case.case_number}-এর চিকিৎসা পরামর্শ বিশেষজ্ঞ দ্বারা আপডেট করা হয়েছে।",
                entity_type="diagnosis_case",
                entity_id=case.id,
                created_at=datetime.now(timezone.utc),
            ))
        else:
            pred_res = await db.execute(
                select(AIPrediction).where(AIPrediction.case_id == case.id).order_by(AIPrediction.created_at.desc()).limit(1)
            )
            latest_pred = pred_res.scalar_one_or_none()
            advisory = Advisory(
                case_id=case.id,
                prediction_id=latest_pred.id if latest_pred else None,
                template_id=None,
                title_bn=title,
                summary_bn=summary_bn,
                detailed_treatment_bn=treatment_bn,
                source=source,
                created_by=expert_user_id,
                is_published=True,
            )
            db.add(advisory)

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

    async def request_expert_review(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        farmer_id: uuid.UUID,
        user_role: str = "farmer",
        **kwargs,
    ) -> DiagnosisCase:
        """
        Farmer explicitly requests expert review for an existing case.
        Creates status history log, assigns available expert, creates CaseAssignment,
        and logs audit trail.
        """
        case = await self._get_case_for_farmer(db, case_id, farmer_id, user_role=user_role)

        if case.status not in ("ai_analyzed", "analyzed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_CASE_STATUS",
                    "message_bn": "শুধুমাত্র AI বিশ্লেষণ সম্পন্ন কেস বিশেষজ্ঞ পর্যালোচনার জন্য অনুরোধ করা যাবে।",
                },
            )

        # Update case status and write to case_status_history
        await self._update_status(
            db,
            case,
            "escalated",
            changed_by=farmer_id,
            notes="Farmer requested expert review",
        )

        # Attempt to assign an available expert who hasn't exceeded max_active_cases
        active_counts_subq = (
            select(
                CaseAssignment.expert_id,
                func.count(CaseAssignment.id).label("active_case_count")
            )
            .join(DiagnosisCase, CaseAssignment.case_id == DiagnosisCase.id)
            .where(
                CaseAssignment.status.in_(["assigned", "in_progress", "pending"]),
                DiagnosisCase.is_deleted == False,
                DiagnosisCase.status.in_(["escalated", "assigned", "in_review"]),
            )
            .group_by(CaseAssignment.expert_id)
            .subquery()
        )

        expert_query = (
            select(
                ExpertProfile,
                func.coalesce(active_counts_subq.c.active_case_count, 0).label("active_count")
            )
            .outerjoin(active_counts_subq, ExpertProfile.user_id == active_counts_subq.c.expert_id)
            .where(
                ExpertProfile.is_available == True,
                func.coalesce(active_counts_subq.c.active_case_count, 0) < ExpertProfile.max_active_cases,
            )
            .order_by(
                func.coalesce(active_counts_subq.c.active_case_count, 0).asc(),  # least busy first
                ExpertProfile.rating.desc(),
            )
            .limit(1)
        )

        expert_result = await db.execute(expert_query)
        expert_row = expert_result.first()
        expert_profile = expert_row[0] if expert_row else None
        if expert_profile:
            case.assigned_expert_id = expert_profile.user_id
            assignment = CaseAssignment(
                case_id=case.id,
                expert_id=expert_profile.user_id,
                assigned_by=farmer_id,
                status="assigned",
                assigned_at=datetime.now(timezone.utc),
            )
            db.add(assignment)
            db.add(
                Notification(
                    user_id=expert_profile.user_id,
                    notification_type="case_assigned",
                    title_bn="নতুন কেস বরাদ্দ",
                    body_bn=f"কেস {case.case_number} আপনার পর্যালোচনার জন্য বরাদ্দ করা হয়েছে।",
                    entity_type="diagnosis_case",
                    entity_id=case.id,
                    created_at=datetime.now(timezone.utc),
                )
            )

        db.add(
            Notification(
                user_id=case.farmer_id,
                notification_type="case_status_changed",
                title_bn="কেস বিশেষজ্ঞের কাছে পাঠানো হয়েছে",
                body_bn=f"কেস {case.case_number} বিশেষজ্ঞের পর্যালোচনার জন্য পাঠানো হয়েছে।",
                entity_type="diagnosis_case",
                entity_id=case.id,
                created_at=datetime.now(timezone.utc),
            )
        )

        # Audit log
        db.add(
            AuditLog(
                user_id=farmer_id,
                action="EXPERT_REVIEW_REQUESTED",
                entity_name="case_mgmt.diagnosis_cases",
                entity_id=case.id,
                new_data={"case_id": str(case.id), "status": "escalated"},
                created_at=datetime.now(timezone.utc),
            )
        )

        await db.flush()
        return case

    # -- Feedback ----------------------------------------------------------

    async def submit_feedback(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        farmer_id: uuid.UUID,
        payload: SubmitFeedbackRequest,
        user_role: str = "farmer",
        **kwargs,
    ) -> AdvisoryFeedback:
        """Record farmer's outcome feedback for the advisory received."""
        # 1. Verify case ownership (farmer only for own case, or agent on their behalf)
        case = await self._get_case_for_farmer(db, case_id, farmer_id, user_role=user_role)
        target_farmer_id = case.farmer_id

        # 2. Find the advisory for this case
        advisory_result = await db.execute(
            select(Advisory).where(Advisory.case_id == case_id)
        )
        advisory = advisory_result.scalar_one_or_none()
        if not advisory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ADVISORY_NOT_FOUND", "message_bn": "এই কেসের জন্য কোনো পরামর্শ পাওয়া যায়নি।"},
            )

        # 3. Check if feedback already exists for this advisory from this farmer
        existing_fb_result = await db.execute(
            select(AdvisoryFeedback).where(
                AdvisoryFeedback.advisory_id == advisory.id,
                AdvisoryFeedback.farmer_id == target_farmer_id,
            )
        )
        feedback = existing_fb_result.scalar_one_or_none()
        if feedback:
            feedback.rating = payload.rating
            feedback.is_helpful = payload.is_helpful
            feedback.feedback_text = payload.feedback_text
            feedback.outcome_status = payload.outcome_status
            feedback.created_at = datetime.now(timezone.utc)
        else:
            feedback = AdvisoryFeedback(
                advisory_id=advisory.id,
                farmer_id=target_farmer_id,
                rating=payload.rating,
                is_helpful=payload.is_helpful,
                feedback_text=payload.feedback_text,
                outcome_status=payload.outcome_status,
                created_at=datetime.now(timezone.utc),
            )
            db.add(feedback)
        await db.flush()
        return feedback

    # -- Helpers -----------------------------------------------------------

    async def _get_case_for_farmer(
        self, db: AsyncSession, case_id: uuid.UUID, farmer_id: uuid.UUID, user_role: str = "farmer", **kwargs
    ) -> DiagnosisCase:
        """Load a case, verifying it belongs to the requesting farmer (or agent/admin/expert)."""
        stmt = select(DiagnosisCase).where(
            DiagnosisCase.id == case_id,
            DiagnosisCase.is_deleted == False,
        )
        allowed_bypass_roles = ("agent", "admin", "administrator", "tech_admin", "technical_admin", "expert")
        if user_role not in allowed_bypass_roles:
            stmt = stmt.where(DiagnosisCase.farmer_id == farmer_id)
        result = await db.execute(stmt)
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

    async def delete_case_with_cleanup(
        self,
        db: AsyncSession,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: str = "farmer",
        background_tasks=None,
        **kwargs,
    ) -> bool:
        """
        Soft-delete diagnosis case and clean up / mark attached files for storage garbage collection.
        Orphaned storage files are deleted asynchronously via background tasks / storage_service.
        """
        case = await self._get_case_for_farmer(db, case_id, user_id, user_role=user_role)
        now_utc = datetime.now(timezone.utc)
        case.is_deleted = True
        case.status = "closed"

        # Load associated case images and files
        images_res = await db.execute(
            select(CaseImage).where(CaseImage.case_id == case.id)
        )
        case_images = images_res.scalars().all()
        file_ids = [img.file_id for img in case_images if img.file_id]

        if file_ids:
            files_res = await db.execute(
                select(SystemFile).where(SystemFile.id.in_(file_ids), SystemFile.is_deleted == False)
            )
            files_to_cleanup = files_res.scalars().all()
            for f in files_to_cleanup:
                # Check if this file is still attached to any other active case
                other_case_using = await db.execute(
                    select(CaseImage)
                    .join(DiagnosisCase, CaseImage.case_id == DiagnosisCase.id)
                    .where(
                        CaseImage.file_id == f.id,
                        CaseImage.case_id != case.id,
                        DiagnosisCase.is_deleted == False,
                    )
                )
                if other_case_using.scalar_one_or_none():
                    continue  # Still referenced by another active case; do not delete

                f.is_deleted = True
                f.deleted_at = now_utc
                # Background cleanup from storage provider
                if background_tasks:
                    background_tasks.add_task(storage_service.delete_file, f.storage_path, f.bucket_name)

        await db.flush()
        return True


diagnosis_service = DiagnosisService()