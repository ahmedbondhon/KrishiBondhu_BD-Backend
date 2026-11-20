import io
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.diagnosis_engine import (
    EngineResult,
    Prediction,
    _prepare_image,
    _extract_json,
    _to_result,
    InvalidImageError,
)
from app.core.dependencies import get_current_user
from app.models.auth import Role, User


def create_dummy_image(format="JPEG", size=(100, 100)):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(73, 109, 137))
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.fixture
def dummy_farmer():
    role = Role(code="farmer", name="কৃষক")
    user = User(
        id="11111111-1111-1111-1111-111111111111",
        phone_number="+8801700000000",
        full_name="Farmer Rahim",
        is_active=True,
    )
    user.role = role
    return user


def test_quick_diagnosis_unsupported_image_type(dummy_farmer):
    app.dependency_overrides[get_current_user] = lambda: dummy_farmer
    client = TestClient(app)

    response = client.post(
        "/api/v1/quick-diagnosis",
        files={"image": ("test.gif", b"GIF89a...", "image/gif")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_IMAGE_TYPE"
    app.dependency_overrides.clear()


def test_quick_diagnosis_empty_image(dummy_farmer):
    app.dependency_overrides[get_current_user] = lambda: dummy_farmer
    client = TestClient(app)

    response = client.post(
        "/api/v1/quick-diagnosis",
        files={"image": ("test.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_IMAGE"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_quick_diagnosis_success_and_cache(dummy_farmer):
    app.dependency_overrides[get_current_user] = lambda: dummy_farmer
    client = TestClient(app)

    img_bytes = create_dummy_image()

    fake_result = EngineResult(
        is_crop_image=True,
        predictions=[
            Prediction(label="rice_blast", confidence=0.85, name_bn="ধানের ব্লাস্ট", name_en="Rice Blast"),
        ],
        urgency="medium",
        crop="rice",
        summary_bn="ধানের ব্লাস্ট রোগ দেখা যাচ্ছে।",
        treatment_bn="আক্রান্ত পাতা অপসারণ করুন।",
        prevention_bn="সুষম সার ব্যবহার করুন।",
    )

    with patch("app.api.v1.quick_diagnosis.diagnose", new_callable=AsyncMock) as mock_diag:
        mock_diag.return_value = fake_result

        # First request (triggers diagnose)
        res1 = client.post(
            "/api/v1/quick-diagnosis",
            files={"image": ("leaf.jpg", img_bytes, "image/jpeg")},
            data={"crop_name": "rice"},
        )
        assert res1.status_code == 200
        data1 = res1.json()["data"]
        assert data1["issue_name_bn"] == "ধানের ব্লাস্ট"
        assert data1["confidence_score"] == 0.85
        assert data1["from_cache"] is False
        assert mock_diag.call_count == 1

        # Second request with same image & crop (should hit cache)
        res2 = client.post(
            "/api/v1/quick-diagnosis",
            files={"image": ("leaf.jpg", img_bytes, "image/jpeg")},
            data={"crop_name": "rice"},
        )
        assert res2.status_code == 200
        data2 = res2.json()["data"]
        assert data2["issue_name_bn"] == "ধানের ব্লাস্ট"
        assert data2["from_cache"] is True
        # diagnose should not have been called again
        assert mock_diag.call_count == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_quick_diagnosis_not_a_crop_image(dummy_farmer):
    app.dependency_overrides[get_current_user] = lambda: dummy_farmer
    client = TestClient(app)

    img_bytes = create_dummy_image()
    fake_result = EngineResult(
        is_crop_image=False,
        predictions=[],
    )

    with patch("app.api.v1.quick_diagnosis.diagnose", new_callable=AsyncMock) as mock_diag:
        mock_diag.return_value = fake_result

        res = client.post(
            "/api/v1/quick-diagnosis",
            files={"image": ("cat.jpg", img_bytes, "image/jpeg")},
        )
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "NOT_A_CROP_IMAGE"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_quick_diagnosis_low_confidence_requires_expert(dummy_farmer):
    app.dependency_overrides[get_current_user] = lambda: dummy_farmer
    client = TestClient(app)

    img_bytes = create_dummy_image(size=(120, 120))
    fake_result = EngineResult(
        is_crop_image=True,
        predictions=[
            Prediction(label="rice_blast", confidence=0.45, name_bn="ধানের ব্লাস্ট", name_en="Rice Blast"),
        ],
        crop="rice",
    )

    with patch("app.api.v1.quick_diagnosis.diagnose", new_callable=AsyncMock) as mock_diag:
        mock_diag.return_value = fake_result

        res = client.post(
            "/api/v1/quick-diagnosis",
            files={"image": ("blurry.jpg", img_bytes, "image/jpeg")},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["requires_expert_review"] is True
        assert data["advisory"] is None
        assert "কৃষি বিশেষজ্ঞের পরামর্শ নিন" in data["notice_bn"]

    app.dependency_overrides.clear()


def test_diagnosis_engine_helpers():
    # Test prepare_image
    valid_img = create_dummy_image(size=(1200, 900))
    jpeg_bytes, mime = _prepare_image(valid_img)
    assert mime == "image/jpeg"
    assert len(jpeg_bytes) > 0

    # Bad image bytes
    with pytest.raises(InvalidImageError):
        _prepare_image(b"not an image")

    # Test extract_json
    raw_text = 'Some prefix text {"is_crop_image": true, "crop": "potato", "predictions": [{"label": "late_blight", "confidence": 0.9}]} suffix'
    data = _extract_json(raw_text)
    assert data["crop"] == "potato"
    assert data["is_crop_image"] is True

    # Test to_result
    res = _to_result(data)
    assert res.is_crop_image is True
    assert res.crop == "potato"
    assert len(res.predictions) == 1
    assert res.predictions[0].label == "late_blight"
    assert res.predictions[0].confidence == 0.9
