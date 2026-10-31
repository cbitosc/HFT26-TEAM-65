"""
Integration Tests for FastAPI REST Endpoints
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)

def test_health_endpoint():
    """Tests GET /api/health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["workspace_drive"] == "D:"
    assert data["benchmark_dataset_loaded"] is True

def test_dataset_summary_endpoint():
    """Tests GET /api/dataset/summary."""
    response = client.get("/api/dataset/summary")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "locations" in data
    assert data["total_images"] > 0

def test_dataset_images_endpoint():
    """Tests GET /api/dataset/images with query params."""
    response = client.get("/api/dataset/images?limit=10&include_empty=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["records"]) <= 10
    assert data["total"] > 0

def test_analytics_overview_endpoint():
    """Tests GET /api/analytics/overview."""
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert "shannon_diversity_index" in data
    assert "empty_rate_pct" in data
    assert "hours_saved" in data

def test_analytics_temporal_endpoint():
    """Tests GET /api/analytics/temporal."""
    response = client.get("/api/analytics/temporal")
    assert response.status_code == 200
    data = response.json()
    assert "hourly_distribution" in data
    assert "diel_classifications" in data

def test_analytics_spatial_endpoint():
    """Tests GET /api/analytics/spatial."""
    response = client.get("/api/analytics/spatial")
    assert response.status_code == 200
    data = response.json()
    assert "stations" in data
    assert "top_co_occurrences" in data

def test_featherless_status_and_summary_endpoint():
    """Tests GET /api/featherless/status and POST /api/featherless/summary."""
    status_resp = client.get("/api/featherless/status")
    assert status_resp.status_code == 200
    
    summary_resp = client.post(
        "/api/featherless/summary",
        json={"custom_instructions": "Check predator overlap"}
    )
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert "summary_markdown" in data

def test_detection_predict_image_endpoint():
    """Tests POST /api/detection/predict-image with simulated image file."""
    # Create simple in-memory image
    img = Image.new("RGB", (256, 192), color=(50, 50, 50))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    
    response = client.post(
        "/api/detection/predict-image",
        files={"file": ("test_camera_frame.jpg", buf, "image/jpeg")},
        data={"location": "loc_03"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "has_animal" in data
    assert "is_empty" in data
    assert "primary_species" in data
    assert "confidence" in data
    assert "bounding_box" in data

def test_delete_gallery_image_endpoint():
    """Tests DELETE /api/dataset/images/{image_id}."""
    response = client.delete("/api/dataset/images/nonexistent_image_id")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["image_id"] == "nonexistent_image_id"

def test_featherless_llm_classify_endpoint():
    """Tests POST /api/featherless/classify with dynamic night routing."""
    # Test night mode routing
    response = client.post(
        "/api/featherless/classify",
        json={"image_data": "data:image/jpeg;base64,mock...", "is_night_mode": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["temperature"] == 0.0
    assert data["is_night_mode"] is True
    assert "CRITICAL OVERRIDE: NIGHT VISION ACTIVE" in data["system_prompt"]
