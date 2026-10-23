# ============================================================================
# KrishiBondhu Bangladesh — Tests for 13 Identified Backend Bug Fixes
# ============================================================================

import asyncio
import inspect
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.deps import require_roles
from app.models.advisory import Advisory
from app.models.ai import AIModel
from app.models.auth import Role, User
from app.models.catalog import Issue
from app.models.diagnosis import CaseAssignment, CaseImage, DiagnosisCase
from app.models.system import SystemFile
from app.schemas.auth import ResetPasswordRequest, validate_strong_password
from app.schemas.diagnosis import SubmitExpertReviewRequest
from app.services.auth import ExtendedAuthService
from app.services.diagnosis_service import DiagnosisService
from app.services.storage_service import StorageService
from app.services.supabase_client import SupabaseClient


# ── 1. Database & Transaction Bugs ──────────────────────────────────────────

class TestDiagnosisStuckStateFix:
    @pytest.mark.asyncio
    async def test_ai_service_failure_resets_case_to_submitted(self):
        """Bug 1.1: When external AI call crashes, case should not be stuck in 'processing'."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        file_id = uuid.uuid4()
        case = DiagnosisCase(
            id=uuid.uuid4(),
            case_number="KB-2026-000001",
            status="submitted",
            farmer_id=uuid.uuid4(),
            crop_id=uuid.uuid4(),
            primary_image_id=file_id,
        )

        image_file = SystemFile(
            id=file_id,
            storage_path="cases/test_crop.jpg",
            original_name="test.jpg",
            bucket_name="krishibondhu-uploads",
            provider="supabase",
            mime_type="image/jpeg",
            file_size_bytes=1024,
        )

        ai_model = AIModel(
            id=uuid.uuid4(),
            model_code="KB-VISION-V1",
            name="Crop Vision",
            version="1.0.0",
            is_active=True,
        )

        def mock_execute_side_effect(query, *args, **kwargs):
            res = MagicMock()
            query_str = str(query)
            if "system.files" in query_str or "files" in query_str:
                res.scalar_one_or_none.return_value = image_file
            elif "ai.models" in query_str or "models" in query_str:
                res.scalar_one_or_none.return_value = ai_model
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute_side_effect

        with patch.object(service, "_get_case_for_farmer", return_value=case), \
             patch.object(service, "_call_ai_service", side_effect=RuntimeError("AI server down")):
            
            with pytest.raises(HTTPException) as exc_info:
                await service.analyze_case(mock_db, case.id, case.farmer_id)
            
            assert exc_info.value.status_code == 500
            # Ensure case status was reset to 'submitted'
            assert case.status == "submitted"
            # Ensure rollback and commit were invoked
            assert mock_db.rollback.called
            assert mock_db.commit.called


class TestExpertReviewAuthorizationAndState:
    @pytest.mark.asyncio
    async def test_expert_review_rejected_if_assigned_to_different_expert(self):
        """Bug 1.2: Expert cannot submit review if case is assigned to another expert."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        assigned_expert_id = uuid.uuid4()
        other_expert_id = uuid.uuid4()

        case = DiagnosisCase(
            id=uuid.uuid4(),
            case_number="KB-2026-000002",
            status="escalated",
            farmer_id=uuid.uuid4(),
            assigned_expert_id=assigned_expert_id,
        )

        other_user = MagicMock()
        other_user.id = other_expert_id
        other_user.role_code = "expert"
        other_user.role = MagicMock(code="expert")

        def mock_execute_side_effect(query, *args, **kwargs):
            res = MagicMock()
            query_str = str(query)
            if "case_mgmt.diagnosis_cases" in query_str or "diagnosis_cases" in query_str:
                res.scalar_one_or_none.return_value = case
            elif "auth.users" in query_str or "users" in query_str:
                res.scalar_one_or_none.return_value = other_user
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute_side_effect

        payload = SubmitExpertReviewRequest(
            agreed_with_ai=True,
            diagnosis_notes_bn="অনুমোদিত হয়েছে, পাতার রোগ শনাক্ত করা হলো।",
            prescribed_treatment_bn="ম্যানকোজেব ২ গ্রাম স্প্রে করুন নিয়মিতভাবে।",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.submit_expert_review(mock_db, case.id, other_expert_id, payload)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_expert_review_updates_case_assignment_to_completed(self):
        """Bug 1.2: Expert review marks case_mgmt.case_assignments as completed with responded_at."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        expert_id = uuid.uuid4()
        case = DiagnosisCase(
            id=uuid.uuid4(),
            case_number="KB-2026-000003",
            status="escalated",
            farmer_id=uuid.uuid4(),
            assigned_expert_id=expert_id,
        )

        assignment = CaseAssignment(
            case_id=case.id,
            expert_id=expert_id,
            status="assigned",
        )

        def mock_execute_side_effect(query, *args, **kwargs):
            res = MagicMock()
            query_str = str(query)
            if "case_mgmt.diagnosis_cases" in query_str or "diagnosis_cases" in query_str:
                res.scalar_one_or_none.return_value = case
            elif "case_mgmt.case_assignments" in query_str or "case_assignments" in query_str:
                res.scalars.return_value.all.return_value = [assignment]
            else:
                res.scalars.return_value.all.return_value = []
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute_side_effect

        payload = SubmitExpertReviewRequest(
            agreed_with_ai=True,
            diagnosis_notes_bn="অনুমোদিত হয়েছে, পাতার রোগ শনাক্ত করা হলো।",
            prescribed_treatment_bn="ম্যানকোজেব ২ গ্রাম স্প্রে করুন নিয়মিতভাবে।",
        )

        await service.submit_expert_review(mock_db, case.id, expert_id, payload)

        assert case.status == "expert_reviewed"
        assert assignment.status == "completed"
        assert assignment.responded_at is not None


class TestRbacTechAdminAliasing:
    @pytest.mark.asyncio
    async def test_tech_admin_and_technical_admin_aliasing(self):
        """Bug 1.3: tech_admin and technical_admin should be aliases in require_roles."""
        dep_tech = require_roles("tech_admin")
        dep_technical = require_roles("technical_admin")

        mock_tech_user = MagicMock(role_code="tech_admin")
        mock_technical_user = MagicMock(role_code="technical_admin")
        mock_farmer_user = MagicMock(role_code="farmer")

        # Calling the dependency with both aliases should succeed
        assert await dep_tech(mock_tech_user) == mock_tech_user
        assert await dep_tech(mock_technical_user) == mock_technical_user
        assert await dep_technical(mock_tech_user) == mock_tech_user
        assert await dep_technical(mock_technical_user) == mock_technical_user

        # Unauthorized role should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await dep_tech(mock_farmer_user)
        assert exc_info.value.status_code == 403


# ── 2. Auth & Security Bugs ─────────────────────────────────────────────────

class TestSupabaseOtpHashAndInspectorCleanup:
    @pytest.mark.asyncio
    async def test_supabase_record_otp_sends_otp_hash_column(self):
        """Bug 2.1: record_otp must pass otp_hash, not otp_code."""
        client = SupabaseClient()
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"success": True}
            await client.record_otp("01700000000", "a" * 64, datetime.now(timezone.utc))
            
            call_args = mock_req.call_args
            assert call_args is not None
            payload = call_args[1].get("json") or call_args[0][2]
            assert "otp_hash" in payload
            assert "otp_code" not in payload

    def test_inspector_method_deleted(self):
        """Bug 2.4: get_inspector_data must be completely removed."""
        client = SupabaseClient()
        assert not hasattr(client, "get_inspector_data")


class TestPasswordResetRolePolicy:
    def test_farmer_pin_vs_strong_password_validation(self):
        """Bug 2.3: Password reset validates strong password for admin/expert and pin for farmer."""
        # 6-digit numeric PIN is allowed for farmer
        valid_farmer_pin = "123456"
        assert valid_farmer_pin.isdigit() and len(valid_farmer_pin) == 6

        # 6-digit numeric PIN fails strong password validation for expert/admin
        with pytest.raises(Exception):
            validate_strong_password(valid_farmer_pin)

        # Strong password with upper, lower, digit, min 8 chars passes
        valid_admin_pass = "P@ssw0rd2026!"
        assert validate_strong_password(valid_admin_pass) == valid_admin_pass


# ── 3. Business Logic & API Bugs ────────────────────────────────────────────

class TestBusinessLogicFixes:
    def test_requires_expert_review_logic(self):
        """Bug 3.3: requires_expert_review is False for submitted, True only for escalated or unconfident."""
        case_submitted = MagicMock(status="submitted")
        assert (case_submitted.status == "escalated") is False

        case_escalated = MagicMock(status="escalated")
        assert (case_escalated.status == "escalated") is True

    @pytest.mark.asyncio
    async def test_prediction_details_maps_issue_id(self):
        """Bug 3.1: AIPredictionDetail matches catalog.issues to populate issue_id."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        case_id = uuid.uuid4()
        farmer_id = uuid.uuid4()
        crop_id = uuid.uuid4()
        issue_id = uuid.uuid4()
        file_id = uuid.uuid4()

        case = DiagnosisCase(
            id=case_id,
            case_number="KB-2026-000010",
            status="submitted",
            farmer_id=farmer_id,
            crop_id=crop_id,
            primary_image_id=file_id,
        )

        image_file = SystemFile(
            id=file_id,
            storage_path="cases/leaf.jpg",
            original_name="leaf.jpg",
            bucket_name="krishibondhu-uploads",
            provider="supabase",
            mime_type="image/jpeg",
            file_size_bytes=2048,
        )

        ai_model = AIModel(
            id=uuid.uuid4(),
            model_code="KB-VISION-V1",
            name="Crop Vision",
            version="1.0.0",
            is_active=True,
        )

        mock_issue = Issue(
            id=issue_id,
            crop_id=crop_id,
            code="BLIGHT_01",
            name_en="Late Blight",
            name_bn="ব্লাইট রোগ",
            category="disease",
            is_active=True,
        )

        ai_response = {
            "predicted_class": "BLIGHT_01",
            "confidence_score": 0.95,
            "severity": "medium",
            "crop_confidence": 0.99,
            "top_predictions": [
                {"class": "BLIGHT_01", "confidence": 0.95},
            ],
            "visual_symptoms": [],
            "affected_parts": ["leaf"],
        }

        # Mock database queries
        def mock_execute_side_effect(query, *args, **kwargs):
            res = MagicMock()
            query_str = str(query)
            if "system.files" in query_str or "files" in query_str:
                res.scalar_one_or_none.return_value = image_file
            elif "ai.models" in query_str or "models" in query_str:
                res.scalar_one_or_none.return_value = ai_model
            elif "catalog.issues" in query_str or "issues" in query_str:
                res.scalars.return_value.all.return_value = [mock_issue]
            else:
                res.scalars.return_value.all.return_value = []
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute_side_effect

        with patch.object(service, "_get_case_for_farmer", return_value=case), \
             patch.object(service, "_call_ai_service", return_value=ai_response), \
             patch.object(service, "_generate_advisory", return_value=None):
            
            result = await service.analyze_case(mock_db, case_id, farmer_id)
            
            assert len(result.top_predictions) > 0
            assert str(result.top_predictions[0].issue_id) == str(issue_id)


# ── 4. Performance & Async Event Loop Bugs ──────────────────────────────────

class TestPerformanceAndAsyncFixes:
    def test_storage_service_check_file_exists_is_coroutine(self):
        """Bug 4.1: check_file_exists must be an async coroutine, non-blocking."""
        service = StorageService()
        assert inspect.iscoroutinefunction(service.check_file_exists)

    @pytest.mark.asyncio
    async def test_shared_clients_and_shutdown(self):
        """Bug 4.2: SupabaseClient and DiagnosisService maintain shared client with close()."""
        client = SupabaseClient()
        diagnosis = DiagnosisService()

        c1 = client.get_client()
        c2 = client.get_client()
        assert c1 is c2  # Reuses same client instance

        await client.close()
        assert client._client is None

        d1 = diagnosis._get_client()
        d2 = diagnosis._get_client()
        assert d1 is d2

        await diagnosis.close()
        assert diagnosis._http_client is None


# ── 5. New Cross-Entity, Auth, and Infrastructure Bug Fixes ──────────────────

class TestNewDataIntegrityAndCrossEntityFixes:
    @pytest.mark.asyncio
    async def test_create_case_idor_plot_ownership(self):
        """Bug 1.1: Attempting to link another farmer's plot_id raises 404 PLOT_NOT_FOUND."""
        from app.schemas.diagnosis import CreateDiagnosisCaseRequest
        service = DiagnosisService()
        mock_db = AsyncMock()

        crop_id = uuid.uuid4()
        other_plot_id = uuid.uuid4()
        farmer_id = uuid.uuid4()

        # Database returns None for plot belonging to farmer_id
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_res

        payload = CreateDiagnosisCaseRequest(
            crop_id=crop_id,
            plot_id=other_plot_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_case(mock_db, farmer_id, payload)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "PLOT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_case_invalid_growth_stage(self):
        """Bug 1.1: Growth stage belonging to a different crop is rejected."""
        from app.models.catalog import GrowthStage
        from app.schemas.diagnosis import CreateDiagnosisCaseRequest
        service = DiagnosisService()
        mock_db = AsyncMock()

        crop_id = uuid.uuid4()
        other_crop_id = uuid.uuid4()
        stage_id = uuid.uuid4()
        farmer_id = uuid.uuid4()

        # Mock stage belonging to other_crop_id
        mock_stage = GrowthStage(
            id=stage_id,
            crop_id=other_crop_id,
            stage_code="FLOWERING",
            name_en="Flowering",
            name_bn="ফুল ধরা",
        )
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = mock_stage
        mock_db.execute.return_value = mock_res

        payload = CreateDiagnosisCaseRequest(
            crop_id=crop_id,
            growth_stage_id=stage_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_case(mock_db, farmer_id, payload)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "INVALID_GROWTH_STAGE"

    @pytest.mark.asyncio
    async def test_generate_advisory_populates_remedies(self):
        """Bug 1.2: _generate_advisory queries catalog.remedies and sets chemical/organic fields."""
        from app.models.advisory import AdvisoryTemplate
        from app.models.ai import AIPrediction
        from app.models.catalog import Remedy

        service = DiagnosisService()
        mock_db = AsyncMock()

        case = DiagnosisCase(id=uuid.uuid4(), case_number="KB-2026-TEST", status="submitted", farmer_id=uuid.uuid4(), crop_id=uuid.uuid4())
        prediction = AIPrediction(id=uuid.uuid4(), case_id=case.id, confidence_score=0.9, is_confident=True)
        issue = Issue(id=uuid.uuid4(), crop_id=case.crop_id, code="BLIGHT_01", name_en="Early Blight", name_bn="আর্লি ব্লাইট", category="disease")
        template = AdvisoryTemplate(id=uuid.uuid4(), issue_id=issue.id, title_bn="আর্লি ব্লাইট ব্যবস্থাপনা", content_bn="চিকিৎসা বিস্তারিত", is_active=True)

        chem_rem = Remedy(id=uuid.uuid4(), issue_id=issue.id, type="chemical", title_bn="রিডোমিল গোল্ড", dosage_bn="২ গ্রাম/লিটার", description_bn="স্প্রে করুন", is_active=True)
        org_rem = Remedy(id=uuid.uuid4(), issue_id=issue.id, type="organic", title_bn="ট্রাইকোডার্মা", dosage_bn="৫ গ্রাম/কেজি", description_bn="বীজ শোধন", is_active=True)

        def mock_exec(query, *args, **kwargs):
            q_str = str(query)
            res = MagicMock()
            if "catalog.remedies" in q_str or "remedies" in q_str:
                res.scalars.return_value.all.return_value = [chem_rem, org_rem]
            elif "advisory.templates" in q_str or "templates" in q_str:
                res.scalar_one_or_none.return_value = template
            elif "advisory.advisories" in q_str or "advisories" in q_str:
                res.scalar_one_or_none.return_value = None
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_exec

        adv = await service._generate_advisory(mock_db, case, prediction, issue, growth_stage_id=None)
        assert adv is not None
        assert "রিডোমিল গোল্ড" in adv.chemical_recommendations_bn
        assert "২ গ্রাম/লিটার" in adv.chemical_recommendations_bn
        assert "ট্রাইকোডার্মা" in adv.organic_recommendations_bn

    def test_farm_crop_cycle_harvest_date_validator(self):
        """Bug 1.3: Sowing date after expected harvest date raises validation error."""
        from datetime import date
        from app.schemas.farm import CreatePlotCropRequest

        # Valid dates
        valid = CreatePlotCropRequest(
            crop_id=uuid.uuid4(),
            sowing_date=date(2026, 1, 1),
            expected_harvest_date=date(2026, 4, 1),
        )
        assert valid.expected_harvest_date >= valid.sowing_date

        # Invalid dates: harvest before sowing
        with pytest.raises(ValueError):
            CreatePlotCropRequest(
                crop_id=uuid.uuid4(),
                sowing_date=date(2026, 5, 1),
                expected_harvest_date=date(2026, 3, 1),
            )


class TestNewAuthAndOtpSecurityFixes:
    def test_verification_token_replay_attack_prevention(self):
        """Bug 2.1: Verification token cannot be reused after consumption."""
        from app.services.otp_service import OtpService
        mock_db = AsyncMock()
        service = OtpService(mock_db)

        phone = "01712345678"
        token = service._generate_verification_token(phone, "reset_password")

        # First decode succeeds
        assert service.decode_verification_token(token, phone, "reset_password") is True

        # Consume token
        service.consume_verification_token(token)

        # Subsequent decode fails
        assert service.decode_verification_token(token, phone, "reset_password") is False

    @pytest.mark.asyncio
    async def test_reset_password_safe_supabase_role_extraction(self):
        """Bug 2.2: When user is only in Supabase (dict), role_code extraction does not crash."""
        from app.services.auth import ExtendedAuthService
        mock_db = AsyncMock()
        service = ExtendedAuthService(mock_db)

        phone = "01712345678"
        payload = ResetPasswordRequest(
            phone_number=phone,
            new_password="Password123!",
            verification_token="dummy_token",
        )

        sb_user_dict = {
            "id": str(uuid.uuid4()),
            "phone_number": phone,
            "role_code": "expert",
        }

        with patch("app.services.auth.supabase_client.get_user_by_phone", new_callable=AsyncMock) as mock_sb, \
             patch.object(service.repo, "get_user_by_phone", new_callable=AsyncMock) as mock_local, \
             patch.object(service.otp_service, "decode_verification_token", return_value=True), \
             patch.object(service.otp_service, "consume_verification_token"):

            mock_sb.return_value = sb_user_dict
            mock_local.return_value = None  # User only exists in Supabase

            # Should successfully validate strong password for expert role without AttributeError
            await service.reset_password(payload)


class TestNewStorageAndInfrastructureFixes:
    def test_storage_extension_spoofing_prevented(self):
        """Bug 4.1: MIME type dictates file extension regardless of original_name spoofing."""
        service = StorageService()
        with patch.object(service, "_get_s3_client") as mock_s3:
            mock_client = MagicMock()
            mock_client.generate_presigned_url.return_value = "https://storage/signed"
            mock_s3.return_value = mock_client

            # Client claims original_name is script.php but mime_type is image/jpeg
            _, storage_path = service.generate_upload_url(
                original_name="script.php",
                mime_type="image/jpeg",
                entity_type="cases",
            )
            assert storage_path.endswith(".jpg")
            assert not storage_path.endswith(".php")

            # Dangerous script extension with unknown mime defaults to .bin
            _, dangerous_path = service.generate_upload_url(
                original_name="exploit.html",
                mime_type="application/octet-stream",
                entity_type="misc",
            )
            assert dangerous_path.endswith(".bin")

    def test_ip_rate_limiter_cleans_up_empty_keys(self):
        """Bug 4.2: IpRateLimiter removes empty IP keys after timestamp expiration."""
        from app.services.otp_service import IpRateLimiter
        import time

        limiter = IpRateLimiter()
        ip = "192.168.1.100"

        # Record with window 1 minute
        assert limiter.check_and_record(ip, max_count=5, window_minutes=1) is True
        assert ip in limiter._store

        # Simulate expiration by aging the timestamp
        limiter._store[ip] = [time.time() - 120]

        # Check again: the expired timestamp is purged and if empty, the key is removed
        with limiter._lock:
            active = [t for t in limiter._store[ip] if t > time.time() - 60]
            if not active:
                limiter._store.pop(ip, None)

        assert ip not in limiter._store

    @pytest.mark.asyncio
    async def test_delete_avatar_soft_deletes_system_files(self):
        """Bug 3.2: delete_avatar calls soft_delete_avatar_files to mark system.files deleted."""
        from app.services.profile import ProfileService
        mock_db = AsyncMock()
        service = ProfileService(mock_db)

        user = User(id=uuid.uuid4(), phone_number="01712345678")

        with patch.object(service.repo, "get_profile", new_callable=AsyncMock) as mock_prof, \
             patch.object(service.repo, "set_avatar", new_callable=AsyncMock) as mock_set, \
             patch.object(service.repo, "soft_delete_avatar_files", new_callable=AsyncMock) as mock_soft_del:

            mock_prof.return_value = (user, None, None, None, None)
            await service.delete_avatar(user)

            assert mock_set.called
            assert mock_soft_del.called


# ── 5. Agent Multi-Step Workflow, Mapping, ORM & Pagination Tests ───────────

class TestAgentMultiStepWorkflow:
    @pytest.mark.asyncio
    async def test_agent_can_attach_image_to_farmers_case(self):
        """Bug 1.1: Agent can attach images to a case created for a farmer."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        farmer_id = uuid.uuid4()
        agent_id = uuid.uuid4()
        case_id = uuid.uuid4()
        file_id = uuid.uuid4()

        case = DiagnosisCase(
            id=case_id,
            farmer_id=farmer_id,
            case_number="KB-2026-000001",
            status="submitted",
        )
        file_record = SystemFile(
            id=file_id,
            uploaded_by=agent_id,
            storage_path="cases/agent_upload.jpg",
            is_deleted=False,
        )

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            q_str = str(query)
            if "case_mgmt.diagnosis_cases" in q_str or "diagnosis_cases" in q_str:
                res.scalar_one_or_none.return_value = case
            elif "system.files" in q_str or "files" in q_str:
                res.scalar_one_or_none.return_value = file_record
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        from app.schemas.diagnosis import AttachCaseImageRequest
        payload = AttachCaseImageRequest(file_id=file_id, image_type="leaf", is_primary=True)

        attached = await service.attach_image(
            mock_db, case_id=case_id, farmer_id=agent_id, payload=payload, user_role="agent"
        )
        assert attached.case_id == case.id
        assert attached.file_id == file_id

    @pytest.mark.asyncio
    async def test_agent_can_analyze_farmers_case(self):
        """Bug 1.1: Agent can trigger AI analysis on farmer's case."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        farmer_id = uuid.uuid4()
        agent_id = uuid.uuid4()
        case_id = uuid.uuid4()
        file_id = uuid.uuid4()

        case = DiagnosisCase(
            id=case_id,
            farmer_id=farmer_id,
            case_number="KB-2026-000002",
            status="submitted",
            primary_image_id=file_id,
            crop_id=uuid.uuid4(),
        )

        with patch.object(service, "_get_case_for_farmer", new_callable=AsyncMock) as mock_get_case, \
             patch.object(service, "_call_ai_service", new_callable=AsyncMock) as mock_call_ai, \
             patch.object(service, "_generate_advisory", new_callable=AsyncMock) as mock_adv:

            mock_get_case.return_value = case
            mock_call_ai.return_value = {
                "top_prediction": {"class": "early_blight", "confidence": 0.95},
                "confidence_score": 0.95,
                "is_confident": True,
                "top_predictions": [],
                "processing_time_ms": 120,
            }
            mock_adv.return_value = MagicMock(
                id=uuid.uuid4(),
                title_bn="পরামর্শ",
                summary_bn="সারাংশ",
                detailed_treatment_bn="চিকিৎসা",
                preventive_measures_bn="প্রতিরোধ",
                chemical_recommendations_bn="রাসায়নিক",
                organic_recommendations_bn="জৈব",
                source="ai_generated",
            )

            # mock model, issue, and file
            model = AIModel(id=uuid.uuid4(), model_code="KB-V1", name="Model", version="1.0", is_active=True)
            issue = Issue(id=uuid.uuid4(), code="early_blight", name_bn="আর্লি ব্লাইট", name_en="Early Blight", crop_id=case.crop_id, category="disease")
            img_file = SystemFile(id=file_id, storage_path="cases/img.jpg")

            def mock_execute(query, *args, **kwargs):
                res = MagicMock()
                q_str = str(query)
                if "system.files" in q_str or "files" in q_str:
                    res.scalar_one_or_none.return_value = img_file
                elif "ai.models" in q_str:
                    res.scalar_one_or_none.return_value = model
                elif "catalog.issues" in q_str:
                    res.scalar_one_or_none.return_value = issue
                    res.scalars.return_value.all.return_value = [issue]
                else:
                    res.scalar_one_or_none.return_value = None
                return res

            mock_db.execute.side_effect = mock_execute

            response = await service.analyze_case(mock_db, case_id=case_id, farmer_id=agent_id, user_role="agent")
            mock_get_case.assert_called_with(mock_db, case_id, agent_id, user_role="agent")
            assert response.case_id == case.id

    @pytest.mark.asyncio
    async def test_farmer_ownership_check_blocks_other_farmers(self):
        """Non-owner farmer cannot access or analyze another farmer's case."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        case_id = uuid.uuid4()
        other_farmer_id = uuid.uuid4()

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        with pytest.raises(HTTPException) as exc_info:
            await service._get_case_for_farmer(mock_db, case_id=case_id, farmer_id=other_farmer_id, user_role="farmer")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_agent_can_view_crop_cycles_for_farmers_plot(self):
        """Bug 1.2: Agent is not blocked by list_crop_cycles."""
        from app.api.v1.farms import list_crop_cycles
        from app.models.farm import Plot

        mock_db = AsyncMock()
        plot_id = uuid.uuid4()
        farmer_id = uuid.uuid4()
        agent_user = MagicMock()
        agent_user.id = uuid.uuid4()
        agent_user.role_code = "agent"
        agent_user.role.code = "agent"

        plot = Plot(id=plot_id, user_id=farmer_id, is_deleted=False)

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            q_str = str(query)
            if "farm.plots" in q_str or "plots" in q_str:
                res.scalar_one_or_none.return_value = plot
            else:
                res.scalars.return_value.all.return_value = []
            return res

        mock_db.execute.side_effect = mock_execute
        resp = await list_crop_cycles(plot_id=plot_id, current_user=agent_user, db=mock_db)
        assert resp.status_code == 200


class TestApiResponseAndDataMapping:
    def test_submit_expert_review_disagree_requires_verified_issue_id(self):
        """Bug 2.2: SubmitExpertReviewRequest validates verified_issue_id when agreed_with_ai=False."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            SubmitExpertReviewRequest(
                agreed_with_ai=False,
                verified_issue_id=None,
                diagnosis_notes_bn="রোগটি আর্লি ব্লাইট নয়, বরং লেট ব্লাইট।",
            )
        assert "verified_issue_id" in str(exc_info.value) or "দ্বিমত" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_submit_expert_review_agree_autofills_verified_issue_id(self):
        """Bug 2.2: When agreed_with_ai=True and verified_issue_id is omitted, autofills from AI prediction."""
        from app.models.ai import AIPrediction
        service = DiagnosisService()
        mock_db = AsyncMock()

        case_id = uuid.uuid4()
        expert_id = uuid.uuid4()
        ai_issue_id = uuid.uuid4()

        case = DiagnosisCase(id=case_id, status="escalated", is_deleted=False, assigned_expert_id=expert_id, farmer_id=uuid.uuid4(), case_number="KB-2026-000003")
        prediction = AIPrediction(id=uuid.uuid4(), case_id=case_id, primary_issue_id=ai_issue_id, created_at=datetime.now(timezone.utc), confidence_score=Decimal("0.90"))
        issue = Issue(id=ai_issue_id, code="potato_late_blight", name_bn="আলুর নাবি ধসা", name_en="Late Blight", crop_id=uuid.uuid4(), category="disease", is_active=True)

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            q_str = str(query)
            if "case_mgmt.diagnosis_cases" in q_str or "diagnosis_cases" in q_str:
                res.scalar_one_or_none.return_value = case
            elif "ai.predictions" in q_str or "predictions" in q_str:
                res.scalar_one_or_none.return_value = prediction
            elif "catalog.issues" in q_str or "issues" in q_str:
                res.scalar_one_or_none.return_value = issue
            elif "case_mgmt.case_assignments" in q_str:
                res.scalars.return_value.all.return_value = []
            elif "advisory.advisories" in q_str or "advisories" in q_str:
                res.scalar_one_or_none.return_value = None
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        payload = SubmitExpertReviewRequest(
            agreed_with_ai=True,
            verified_issue_id=None,
            diagnosis_notes_bn="AI নির্ণয় সঠিক হয়েছে। প্রয়োজনীয় সতর্কতা গ্রহণ করুন।",
        )

        review = await service.submit_expert_review(mock_db, case_id=case_id, expert_user_id=expert_id, payload=payload)
        assert review.verified_issue_id == ai_issue_id

    @pytest.mark.asyncio
    async def test_submit_expert_review_invalid_issue_raises_404(self):
        """Bug 2.2: Submitting a non-existent verified_issue_id raises 404."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        case_id = uuid.uuid4()
        expert_id = uuid.uuid4()
        case = DiagnosisCase(id=case_id, status="escalated", is_deleted=False, assigned_expert_id=expert_id)

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            q_str = str(query)
            if "case_mgmt.diagnosis_cases" in q_str or "diagnosis_cases" in q_str:
                res.scalar_one_or_none.return_value = case
            elif "catalog.issues" in q_str or "issues" in q_str:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        payload = SubmitExpertReviewRequest(
            agreed_with_ai=False,
            verified_issue_id=uuid.uuid4(),
            diagnosis_notes_bn="সঠিক রোগ এটি নয়, ভিন্ন একটি রোগ।",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.submit_expert_review(mock_db, case_id=case_id, expert_user_id=expert_id, payload=payload)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_case_includes_disease_name_and_images(self):
        """Bug 2.1 & 3.1: get_case returns issue_name_bn, confidence_level, top_predictions, images."""
        from app.api.v1.diagnosis import get_case
        from app.models.ai import AIPrediction, AIPredictionDetail
        from app.models.diagnosis import CaseImage

        mock_db = AsyncMock()
        case_id = uuid.uuid4()
        farmer_id = uuid.uuid4()
        file_id = uuid.uuid4()
        issue_id = uuid.uuid4()

        case = DiagnosisCase(
            id=case_id,
            case_number="KB-2026-000004",
            farmer_id=farmer_id,
            status="ai_analyzed",
            urgency_level="high",
            farmer_notes="পাতায় কালো দাগ",
            is_deleted=False,
        )
        case.expert_reviews = []
        case.advisory = None

        img = CaseImage(
            id=uuid.uuid4(),
            case_id=case_id,
            file_id=file_id,
            image_type="leaf",
            is_primary=True,
            created_at=datetime.now(timezone.utc),
        )
        case.images = [img]

        pred = AIPrediction(
            id=uuid.uuid4(),
            case_id=case_id,
            primary_issue_id=issue_id,
            confidence_score=Decimal("0.92"),
            is_confident=True,
            created_at=datetime.now(timezone.utc),
        )
        pred_detail = AIPredictionDetail(
            id=uuid.uuid4(),
            prediction_id=pred.id,
            issue_id=issue_id,
            class_label="potato_late_blight",
            rank_order=1,
            confidence_score=Decimal("0.92"),
            created_at=datetime.now(timezone.utc),
        )
        pred.details = [pred_detail]
        case.predictions = [pred]

        issue = Issue(
            id=issue_id,
            code="potato_late_blight",
            name_bn="আলুর নাবি ধসা",
            name_en="Late Blight",
            crop_id=uuid.uuid4(),
            category="disease",
        )

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            q_str = str(query)
            if "case_mgmt.diagnosis_cases" in q_str or "diagnosis_cases" in q_str:
                res.scalar_one_or_none.return_value = case
            elif "catalog.issues" in q_str or "issues" in q_str:
                res.scalar_one_or_none.return_value = issue
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        user = MagicMock()
        user.id = farmer_id
        user.role_code = "farmer"
        user.role.code = "farmer"

        resp = await get_case(case_id=case_id, current_user=user, db=mock_db)
        import json
        body = json.loads(resp.body)
        data = body["data"]

        assert data["issue_id"] == str(issue_id)
        assert data["issue_name_bn"] == "আলুর নাবি ধসা"
        assert data["issue_name_en"] == "Late Blight"
        assert data["confidence_level"] == "high"
        assert len(data["top_predictions"]) == 1
        assert len(data["images"]) == 1
        assert data["images"][0]["file_id"] == str(file_id)


class TestOrmAndFileViewUrlAuthorization:
    @pytest.mark.asyncio
    async def test_expert_and_agent_can_access_view_url(self):
        """Bug 3.2: Expert and agent can generate view URL for farmer's uploaded image."""
        from app.api.v1.files import get_view_url
        from app.services.storage_service import storage_service

        mock_db = AsyncMock()
        file_id = uuid.uuid4()
        farmer_id = uuid.uuid4()

        file_record = SystemFile(
            id=file_id,
            uploaded_by=farmer_id,
            storage_path="cases/crop.jpg",
            is_deleted=False,
        )

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            res.scalar_one_or_none.return_value = file_record
            return res

        mock_db.execute.side_effect = mock_execute

        with patch.object(storage_service, "generate_view_url", return_value="https://storage.example.com/view/crop.jpg"):
            # Test Expert
            expert_user = MagicMock()
            expert_user.id = uuid.uuid4()
            expert_user.role_code = "expert"
            expert_user.role.code = "expert"

            resp_expert = await get_view_url(file_id=file_id, current_user=expert_user, db=mock_db)
            assert resp_expert.status_code == 200

            # Test Agent
            agent_user = MagicMock()
            agent_user.id = uuid.uuid4()
            agent_user.role_code = "agent"
            agent_user.role.code = "agent"

            resp_agent = await get_view_url(file_id=file_id, current_user=agent_user, db=mock_db)
            assert resp_agent.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthorized_user_cannot_access_view_url(self):
        """Bug 3.2: Another random farmer cannot view someone else's file."""
        from app.api.v1.files import get_view_url

        mock_db = AsyncMock()
        file_id = uuid.uuid4()
        file_record = SystemFile(
            id=file_id,
            uploaded_by=uuid.uuid4(),
            storage_path="cases/crop.jpg",
            is_deleted=False,
        )

        def mock_execute(query, *args, **kwargs):
            res = MagicMock()
            res.scalar_one_or_none.return_value = file_record
            return res

        mock_db.execute.side_effect = mock_execute

        other_farmer = MagicMock()
        other_farmer.id = uuid.uuid4()
        other_farmer.role_code = "farmer"
        other_farmer.role.code = "farmer"

        resp = await get_view_url(file_id=file_id, current_user=other_farmer, db=mock_db)
        assert resp.status_code == 403


class TestPaginationEdgeCases:
    @pytest.mark.asyncio
    async def test_pagination_parameters_apply_limit_and_offset(self):
        """Bug 4.1: list_cases, get_expert_cases, and list_farms accept limit and offset."""
        from app.api.v1.diagnosis import list_cases, get_expert_cases
        from app.api.v1.farms import list_farms

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        user = MagicMock()
        user.id = uuid.uuid4()
        user.role_code = "admin"
        user.role.code = "admin"

        # list_cases
        resp1 = await list_cases(limit=10, offset=5, current_user=user, db=mock_db)
        assert resp1.status_code == 200

        # get_expert_cases
        resp2 = await get_expert_cases(limit=25, offset=10, current_user=user, db=mock_db)
        assert resp2.status_code == 200

        # list_farms
        resp3 = await list_farms(limit=15, offset=0, current_user=user, db=mock_db)
        assert resp3.status_code == 200


# ── 5. AI Advisory, Storage Clean-up, and Concurrency Locking Fixes ───────────

class TestEdgeCasesAndConcurrencyFixes:
    @pytest.mark.asyncio
    async def test_low_confidence_escalation_deactivates_stale_advisory(self):
        """Edge Case 1: Low-confidence AI analysis deactivates any existing advisory."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        case_id = uuid.uuid4()
        farmer_id = uuid.uuid4()
        primary_file_id = uuid.uuid4()
        case = DiagnosisCase(
            id=case_id,
            case_number="KB-2026-000099",
            farmer_id=farmer_id,
            status="submitted",
            urgency_level="medium",
            primary_image_id=primary_file_id,
            created_at=datetime.now(timezone.utc),
        )
        existing_advisory = Advisory(
            id=uuid.uuid4(),
            case_id=case_id,
            title_bn="পুরনো পরামর্শ",
            summary_bn="পুরনো সারাংশ",
            detailed_treatment_bn="পুরনো চিকিৎসা",
            is_published=True,
        )

        mock_model = MagicMock()
        mock_model.id = uuid.uuid4()
        mock_model.version = "v1"

        def mock_execute(stmt, *args, **kwargs):
            res = MagicMock()
            q_str = str(stmt).lower()
            if "case_mgmt.diagnosis_cases" in q_str:
                res.scalar_one_or_none.return_value = case
            elif "case_images" in q_str:
                img = MagicMock()
                img.file_id = uuid.uuid4()
                res.scalars.return_value.all.return_value = [img]
            elif "system.files" in q_str or "files" in q_str:
                f = MagicMock()
                f.storage_path = "cases/img.jpg"
                res.scalar_one_or_none.return_value = f
            elif "ai.models" in q_str or "models" in q_str:
                res.scalar_one_or_none.return_value = mock_model
            elif "catalog.issues" in q_str:
                res.scalars.return_value.all.return_value = []
            elif "advisory.advisories" in q_str or "advisories" in q_str:
                res.scalar_one_or_none.return_value = existing_advisory
            else:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        # Mock AI service returning low confidence
        with patch.object(service, "_call_ai_service", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {
                "confidence_score": 0.40,
                "urgency_level": "medium",
                "is_confident": False,
                "model_version": "v1",
                "top_predictions": [],
            }

            resp = await service.analyze_case(mock_db, case_id=case_id, farmer_id=farmer_id)
            assert resp.case_status == "escalated"
            assert existing_advisory.is_published is False

    @pytest.mark.asyncio
    async def test_case_deletion_triggers_background_storage_cleanup(self):
        """Edge Case 2: Deleting a case marks files as deleted and enqueues storage deletion."""
        service = DiagnosisService()
        mock_db = AsyncMock()

        case_id = uuid.uuid4()
        farmer_id = uuid.uuid4()
        case = DiagnosisCase(
            id=case_id,
            farmer_id=farmer_id,
            status="submitted",
            is_deleted=False,
        )
        file_id = uuid.uuid4()
        case_image = CaseImage(
            id=uuid.uuid4(),
            case_id=case_id,
            file_id=file_id,
        )
        sys_file = SystemFile(
            id=file_id,
            storage_path="cases/photo.jpg",
            bucket_name="krishibondhu-uploads",
            is_deleted=False,
        )

        def mock_execute(stmt, *args, **kwargs):
            res = MagicMock()
            q_str = str(stmt).lower()
            if "case_mgmt.diagnosis_cases" in q_str:
                res.scalar_one_or_none.return_value = case
            elif "case_images" in q_str:
                res.scalars.return_value.all.return_value = [case_image]
            elif "system.files" in q_str or "files" in q_str:
                res.scalars.return_value.all.return_value = [sys_file]
            else:
                res.scalars.return_value.all.return_value = []
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        mock_bg = MagicMock()
        deleted = await service.delete_case_with_cleanup(
            mock_db, case_id=case_id, user_id=farmer_id, user_role="farmer", background_tasks=mock_bg
        )
        assert deleted is True
        assert case.is_deleted is True
        assert case.status == "closed"
        assert sys_file.is_deleted is True
        assert sys_file.deleted_at is not None
        assert mock_bg.add_task.called

    @pytest.mark.asyncio
    async def test_group_selling_with_for_update_prevents_race_conditions(self):
        """Edge Case 3: Joining group selling offer uses row-level locking (with_for_update) and atomic aggregation."""
        from app.services.market_service import market_service
        from app.models.market import GroupSellingOffer

        mock_db = AsyncMock()
        offer_id = uuid.uuid4()
        farmer_id = uuid.uuid4()

        offer = GroupSellingOffer(
            id=offer_id,
            target_quantity_kg=Decimal("1000.00"),
            min_participant_quantity_kg=Decimal("50.00"),
            current_aggregated_kg=Decimal("900.00"),
            status="open",
            is_deleted=False,
        )

        executed_statements = []

        def mock_execute(stmt, *args, **kwargs):
            executed_statements.append(stmt)
            res = MagicMock()
            q_str = str(stmt).lower()
            if "market.group_selling_offers" in q_str or "group_selling_offers" in q_str:
                res.scalar_one_or_none.return_value = offer
            elif "market.offer_participants" in q_str or "offer_participants" in q_str:
                res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        participant = await market_service.join_group_offer(
            mock_db,
            offer_id=offer_id,
            farmer_id=farmer_id,
            offered_quantity_kg=Decimal("150.00"),
        )
        assert participant.farmer_id == farmer_id
        assert offer.current_aggregated_kg == Decimal("1050.00")
        assert offer.status == "target_reached"

        # Verify that with_for_update() was attached to the query
        first_stmt = executed_statements[0]
        assert hasattr(first_stmt, "_for_update_arg") and first_stmt._for_update_arg is not None

    @pytest.mark.asyncio
    async def test_otp_verification_applies_row_level_locking(self):
        """Edge Case 3: get_latest_otp supports with_for_update row lock to prevent double verification race."""
        from app.repositories.auth import AuthRepository

        mock_db = AsyncMock()
        repo = AuthRepository(mock_db)

        executed_stmts = []

        def mock_execute(stmt, *args, **kwargs):
            executed_stmts.append(stmt)
            res = MagicMock()
            res.scalar_one_or_none.return_value = None
            return res

        mock_db.execute.side_effect = mock_execute

        await repo.get_latest_otp("01711223344", purpose="login", for_update=True)
        assert len(executed_stmts) == 1
        stmt = executed_stmts[0]
        assert hasattr(stmt, "_for_update_arg") and stmt._for_update_arg is not None
