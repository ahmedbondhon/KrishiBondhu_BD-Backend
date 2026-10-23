# ============================================================================
# KrishiBondhu Bangladesh — Farmer Profile API Tests
# Tests for:
#   1. View Profile (GET /api/v1/farmer/profile) with LEFT JOIN geo names & meta
#   2. Edit Profile (PUT /api/v1/farmer/profile) with dynamic update & phone immutability
#   3. Avatar Upload (POST /api/v1/farmer/profile/avatar) with size, mime, collision-free naming
#   4. Avatar Delete (DELETE /api/v1/farmer/profile/avatar)
#   5. Static file serving configuration
# ============================================================================

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.main import app
from app.models.auth import Role, User
from app.models.geo import District, Division, Union, Upazila
from app.models.system import File
from app.repositories.profile import ProfileRepository
from app.services.profile import ProfileService

settings = get_settings()
client = TestClient(app)


# Mock user fixture
@pytest.fixture
def mock_farmer():
    user = User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        phone_number="01712345678",
        full_name="করিম মিয়া",
        role_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        preferred_language="bn",
        avatar_url=None,
        division_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        district_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        upazila_id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
        union_id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
        is_active=True,
        is_deleted=False,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    user.role = Role(code="farmer", name="Farmer")
    return user


@pytest.fixture
def mock_geo():
    div = Division(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        bbs_code="30",
        name_en="Dhaka",
        name_bn="ঢাকা",
        is_active=True,
    )
    dist = District(
        id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        division_id=div.id,
        bbs_code="3026",
        name_en="Gazipur",
        name_bn="গাজীপুর",
        is_active=True,
    )
    upa = Upazila(
        id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
        district_id=dist.id,
        bbs_code="302637",
        name_en="Kaliakair",
        name_bn="কালিয়াকৈর",
        is_active=True,
    )
    uni = Union(
        id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
        upazila_id=upa.id,
        bbs_code="30263715",
        name_en="Boali",
        name_bn="বোয়ালী",
        is_active=True,
    )
    return div, dist, upa, uni


class TestFarmerProfileView:
    """ধাপ ২: ডেটা প্রদর্শন API (View Profile - GET /api/v1/farmer/profile)"""

    def test_view_profile_unauthorized(self):
        """Unauthenticated request must be rejected with 401."""
        app.dependency_overrides.pop(get_current_user, None)
        res = client.get("/api/v1/farmer/profile")
        assert res.status_code == 401

    def test_view_profile_success_with_geo_names(self, mock_farmer, mock_geo):
        """Profile view must return Bangla/English names for divisions/districts and IDs in meta."""
        div, dist, upa, uni = mock_geo

        async def override_current_user():
            return mock_farmer

        app.dependency_overrides[get_current_user] = override_current_user

        with patch.object(
            ProfileRepository,
            "get_profile",
            new=AsyncMock(return_value=(mock_farmer, div, dist, upa, uni)),
        ):
            res = client.get("/api/v1/farmer/profile")
            assert res.status_code == 200
            data = res.json()

            # Basic farmer info
            assert data["id"] == str(mock_farmer.id)
            assert data["full_name"] == "করিম মিয়া"
            assert data["phone_number"] == "01712345678"
            assert data["preferred_language"] == "bn"

            # Geo display fields must contain Bangla and English names
            assert data["division"] == {"name_bn": "ঢাকা", "name_en": "Dhaka"}
            assert data["district"] == {"name_bn": "গাজীপুর", "name_en": "Gazipur"}
            assert data["upazila"] == {"name_bn": "কালিয়াকৈর", "name_en": "Kaliakair"}
            assert data["union"] == {"name_bn": "বোয়ালী", "name_en": "Boali"}

            # Meta object must contain raw UUIDs for frontend dropdown selectors
            assert data["meta"]["division_id"] == str(div.id)
            assert data["meta"]["district_id"] == str(dist.id)
            assert data["meta"]["upazila_id"] == str(upa.id)
            assert data["meta"]["union_id"] == str(uni.id)

    def test_view_profile_handles_null_geo(self, mock_farmer):
        """Profile view must handle null geo fields gracefully."""
        mock_farmer.division_id = None
        mock_farmer.district_id = None
        mock_farmer.upazila_id = None
        mock_farmer.union_id = None

        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        with patch.object(
            ProfileRepository,
            "get_profile",
            new=AsyncMock(return_value=(mock_farmer, None, None, None, None)),
        ):
            res = client.get("/api/v1/farmer/profile")
            assert res.status_code == 200
            data = res.json()

            assert data["division"] is None
            assert data["district"] is None
            assert data["upazila"] is None
            assert data["union"] is None
            assert data["meta"]["division_id"] is None


class TestFarmerProfileEdit:
    """ধাপ ৩: তথ্য এডিট করার API (Edit Profile - PUT /api/v1/farmer/profile)"""

    def test_edit_profile_success(self, mock_farmer, mock_geo):
        """Updating name and language returns success message and updated profile."""
        div, dist, upa, uni = mock_geo
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        updated_farmer = mock_farmer
        updated_farmer.full_name = "আব্দুর রহমান"
        updated_farmer.preferred_language = "en"

        with patch.object(
            ProfileRepository,
            "get_profile",
            new=AsyncMock(return_value=(mock_farmer, div, dist, upa, uni)),
        ), patch.object(
            ProfileRepository,
            "update_profile",
            new=AsyncMock(return_value=(updated_farmer, div, dist, upa, uni)),
        ) as mock_update:
            payload = {"fullName": "আব্দুর রহমান", "preferredLanguage": "en"}
            res = client.put("/api/v1/farmer/profile", json=payload)
            assert res.status_code == 200
            data = res.json()

            assert "সফলভাবে" in data["message"] or "successfully" in data["message"]
            assert data["profile"]["full_name"] == "আব্দুর রহমান"
            assert data["profile"]["preferred_language"] == "en"

            # Verify repository received only modified fields
            called_args = mock_update.call_args[0]
            assert called_args[0] == mock_farmer.id
            assert "full_name" in called_args[1]
            assert "preferred_language" in called_args[1]

    def test_edit_profile_phone_number_is_immutable(self, mock_farmer):
        """Security Rule: phone number is immutable and cannot be updated."""
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        payload = {"phoneNumber": "01799999999", "fullName": "নতুন নাম"}
        res = client.put("/api/v1/farmer/profile", json=payload)
        # Should be rejected with 422 (forbidden extra) or 400
        assert res.status_code in (400, 422)

    def test_edit_profile_empty_payload_rejected(self, mock_farmer):
        """Submitting an empty update body must return 400."""
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        res = client.put("/api/v1/farmer/profile", json={})
        assert res.status_code == 400

    def test_edit_profile_geo_hierarchy_mismatch_rejected(self, mock_farmer, mock_geo):
        """District that does not belong to the selected division must be rejected."""
        div, dist, upa, uni = mock_geo
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        with patch.object(
            ProfileRepository,
            "get_profile",
            new=AsyncMock(return_value=(mock_farmer, div, dist, upa, uni)),
        ), patch.object(
            ProfileRepository,
            "check_geo_exists",
            new=AsyncMock(return_value=False),  # Simulates hierarchy check failure
        ):
            payload = {
                "divisionId": str(div.id),
                "districtId": str(uuid.uuid4()),  # Invalid district for this division
            }
            res = client.put("/api/v1/farmer/profile", json=payload)
            assert res.status_code == 400
            err = res.json()
            assert "বিভাগের" in err["detail"] or "division" in err["detail"].lower()


class TestFarmerAvatarHandling:
    """ধাপ ৪ ও ৫: প্রোফাইল পিকচার আপলোড, মুছে ফেলা ও স্ট্যাটিক কনফিগারেশন"""

    def test_upload_avatar_success(self, mock_farmer, mock_geo, tmp_path):
        """Valid JPEG image upload stores file, creates system.files record, and updates avatar_url."""
        div, dist, upa, uni = mock_geo
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF" + (b"\x00" * 100)  # valid JPEG header

        with patch.object(
            ProfileRepository,
            "get_profile",
            new=AsyncMock(return_value=(mock_farmer, div, dist, upa, uni)),
        ), patch.object(
            ProfileRepository,
            "set_avatar",
            new=AsyncMock(),
        ) as mock_set_avatar, patch.object(
            ProfileRepository,
            "record_avatar_file",
            new=AsyncMock(),
        ) as mock_record_file, patch(
            "app.services.profile.supabase_client.upload_storage_file",
            new=AsyncMock(return_value=f"https://damfsrzakxxccalogghh.supabase.co/storage/v1/object/public/{settings.storage_bucket_name}/avatars/test.jpg"),
        ):
            files = {"file": ("my_avatar.jpg", io.BytesIO(fake_image), "image/jpeg")}
            res = client.post("/api/v1/farmer/profile/avatar", files=files)
            assert res.status_code == 201
            data = res.json()

            assert "আপলোড হয়েছে" in data["message"] or "uploaded" in data["message"].lower()
            assert "profile" in data

            # Verify set_avatar was called with public URL
            mock_set_avatar.assert_called_once()
            user_id_arg, avatar_url_arg = mock_set_avatar.call_args[0]
            assert user_id_arg == mock_farmer.id
            assert "avatars/" in avatar_url_arg

            # Verify record_avatar_file was called for system.files
            mock_record_file.assert_called_once()
            record_kwargs = mock_record_file.call_args[1]
            assert record_kwargs["user_id"] == mock_farmer.id
            assert record_kwargs["bucket_name"] == settings.storage_bucket_name
            assert record_kwargs["provider"] == settings.storage_provider
            assert record_kwargs["mime_type"] == "image/jpeg"
            assert "/avatars/" in record_kwargs["storage_path"]

    def test_upload_avatar_invalid_mime_rejected(self, mock_farmer):
        """Non-image files (e.g. PDF or plain text) must be rejected with 400."""
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        files = {"file": ("document.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
        res = client.post("/api/v1/farmer/profile/avatar", files=files)
        assert res.status_code == 400
        assert "JPEG" in res.json()["detail"] or "image" in res.json()["detail"].lower()

    def test_upload_avatar_oversized_file_rejected(self, mock_farmer):
        """File larger than 2MB must be rejected with 400."""
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        oversized_data = b"0" * (2 * 1024 * 1024 + 10)  # > 2MB
        files = {"file": ("big.png", io.BytesIO(oversized_data), "image/png")}
        res = client.post("/api/v1/farmer/profile/avatar", files=files)
        assert res.status_code == 400
        assert "২" in res.json()["detail"] or "2MB" in res.json()["detail"]

    def test_upload_avatar_empty_file_rejected(self, mock_farmer):
        """0-byte file must be rejected with 400."""
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        files = {"file": ("empty.png", io.BytesIO(b""), "image/png")}
        res = client.post("/api/v1/farmer/profile/avatar", files=files)
        assert res.status_code == 400

    def test_delete_avatar_success(self, mock_farmer):
        """Deleting avatar sets avatar_url to NULL in auth.users and returns success message."""
        app.dependency_overrides[get_current_user] = lambda: mock_farmer

        with patch.object(
            ProfileRepository,
            "get_profile",
            new=AsyncMock(return_value=(mock_farmer, None, None, None, None)),
        ), patch.object(
            ProfileRepository,
            "set_avatar",
            new=AsyncMock(),
        ) as mock_set_avatar:
            res = client.delete("/api/v1/farmer/profile/avatar")
            assert res.status_code == 200
            data = res.json()

            assert "মুছে ফেলা হয়েছে" in data["message"] or "deleted" in data["message"].lower()
            mock_set_avatar.assert_called_once_with(mock_farmer.id, None)

    def test_static_avatar_file_serving(self):
        """Static directory must serve stored avatars."""
        avatars_dir = Path(settings.upload_dir) / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)
        test_file = avatars_dir / "test_avatar_sample.txt"
        test_file.write_text("avatar-content-sample")

        res = client.get("/static/avatars/test_avatar_sample.txt")
        assert res.status_code == 200
        assert res.text == "avatar-content-sample"

        test_file.unlink(missing_ok=True)
