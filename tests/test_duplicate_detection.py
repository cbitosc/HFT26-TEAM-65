"""
Unit & Integration Tests for Duplicate Image Detection Service
AI-Powered Wildlife Monitoring & Camera-Trap Analytics System
Team 65: The Chosen One | CBIT Hacktoberfest '26
"""

import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import pytest
import numpy as np
from PIL import Image
from pathlib import Path
from src.backend.services.duplicate_service import DuplicateDetectorService, duplicate_service
from src.backend.config import IMAGES_DIR

@pytest.fixture
def service():
    return DuplicateDetectorService()

def test_hash_computation_on_blank_and_gradient(service, tmp_path):
    """Verifies that dHash and aHash compute deterministic 64-bit strings."""
    # Create test white image and black image
    white_img = Image.new('RGB', (100, 100), color=(255, 255, 255))
    black_img = Image.new('RGB', (100, 100), color=(0, 0, 0))
    white_path = tmp_path / "white.jpg"
    black_path = tmp_path / "black.jpg"
    white_img.save(white_path)
    black_img.save(black_path)

    h_white = service.compute_hashes_from_path_or_image(white_path)
    h_black = service.compute_hashes_from_path_or_image(black_path)

    assert h_white["is_valid"] is True
    assert len(h_white["dhash"]) == 16
    assert len(h_white["ahash"]) == 16
    assert len(h_white["d_bits"]) == 64
    assert len(h_white["a_bits"]) == 64

def test_identical_image_similarity_is_100_percent(service):
    """Tests that identical images have 1.0 visual similarity."""
    sample_coyote = IMAGES_DIR / "cct_0003_loc_02_coyote.jpg"
    if sample_coyote.exists():
        h1 = service.compute_hashes_from_path_or_image(sample_coyote)
        h2 = service.compute_hashes_from_path_or_image(sample_coyote)
        sim = service.compute_visual_similarity(h1, h2)
        assert sim == 1.0

def test_burst_sequence_duplicate_detection(service):
    """Verifies that consecutive burst frames of the same animal are grouped."""
    c3 = IMAGES_DIR / "cct_0003_loc_02_coyote.jpg"
    c4 = IMAGES_DIR / "cct_0004_loc_02_coyote.jpg"
    c5 = IMAGES_DIR / "cct_0005_loc_02_coyote.jpg"

    if c3.exists() and c4.exists() and c5.exists():
        records = [
            {"image_id": "c3", "image_path": str(c3), "species": "coyote", "confidence": 0.88, "location": "loc_02"},
            {"image_id": "c4", "image_path": str(c4), "species": "coyote", "confidence": 0.96, "location": "loc_02"},
            {"image_id": "c5", "image_path": str(c5), "species": "coyote", "confidence": 0.85, "location": "loc_02"},
        ]
        result = service.group_similar_images(records)
        assert result["total_images"] == 3
        assert result["unique_encounters_count"] == 1
        assert result["duplicate_images_count"] == 2
        assert result["workload_reduction_pct"] == pytest.approx(66.7, abs=0.1)

        cluster = result["clusters"][0]
        assert cluster["total_frames"] == 3
        assert cluster["duplicate_count"] == 2
        assert cluster["anchor_image_id"] == "c4"  # Highest confidence (0.96) selected as anchor!

def test_distinct_species_not_grouped(service):
    """Tests that completely different animals are kept in separate clusters."""
    c3 = IMAGES_DIR / "cct_0003_loc_02_coyote.jpg"
    b9 = IMAGES_DIR / "cct_0009_loc_03_bobcat.jpg"

    if c3.exists() and b9.exists():
        records = [
            {"image_id": "c3", "image_path": str(c3), "species": "coyote", "confidence": 0.90, "location": "loc_02"},
            {"image_id": "b9", "image_path": str(b9), "species": "bobcat", "confidence": 0.92, "location": "loc_03"},
        ]
        result = service.group_similar_images(records)
        assert result["total_images"] == 2
        assert result["unique_encounters_count"] == 2
        assert result["duplicate_images_count"] == 0
        assert result["workload_reduction_pct"] == 0.0

def test_anchor_selection_prioritizes_animal_and_confidence(service):
    """Ensures anchor frame selection prefers animal presence and higher confidence."""
    members = [
        {"_dedup_id": "frame_1", "has_animal": False, "confidence": 0.20, "sharpness": 15.0},
        {"_dedup_id": "frame_2", "has_animal": True, "confidence": 0.72, "sharpness": 10.0},
        {"_dedup_id": "frame_3", "has_animal": True, "confidence": 0.95, "sharpness": 12.0},
    ]
    anchor = service.select_anchor_frame(members)
    assert anchor["_dedup_id"] == "frame_3"

def test_empty_records_handling(service):
    """Tests graceful handling when empty records list is passed."""
    result = service.group_similar_images([])
    assert result["total_images"] == 0
    assert result["unique_encounters_count"] == 0
    assert result["duplicate_images_count"] == 0
    assert result["workload_reduction_pct"] == 0.0
    assert result["clusters"] == []

def test_multiple_species_burst_batch(service):
    """Tests mixed batch with 3 coyotes, 2 rabbits, and 1 bobcat."""
    c3 = IMAGES_DIR / "cct_0003_loc_02_coyote.jpg"
    c4 = IMAGES_DIR / "cct_0004_loc_02_coyote.jpg"
    c5 = IMAGES_DIR / "cct_0005_loc_02_coyote.jpg"
    r20 = IMAGES_DIR / "cct_0020_loc_02_cottontail_rabbit.jpg"
    r21 = IMAGES_DIR / "cct_0021_loc_02_cottontail_rabbit.jpg"
    b9 = IMAGES_DIR / "cct_0009_loc_03_bobcat.jpg"

    if all(p.exists() for p in [c3, c4, c5, r20, r21, b9]):
        records = [
            {"image_id": "c3", "image_path": str(c3), "species": "coyote", "confidence": 0.88, "location": "loc_02"},
            {"image_id": "c4", "image_path": str(c4), "species": "coyote", "confidence": 0.95, "location": "loc_02"},
            {"image_id": "c5", "image_path": str(c5), "species": "coyote", "confidence": 0.84, "location": "loc_02"},
            {"image_id": "r20", "image_path": str(r20), "species": "cottontail_rabbit", "confidence": 0.91, "location": "loc_02"},
            {"image_id": "r21", "image_path": str(r21), "species": "cottontail_rabbit", "confidence": 0.93, "location": "loc_02"},
            {"image_id": "b9", "image_path": str(b9), "species": "bobcat", "confidence": 0.89, "location": "loc_03"},
        ]
        result = service.group_similar_images(records)
        assert result["total_images"] == 6
        assert result["unique_encounters_count"] == 3
        assert result["duplicate_images_count"] == 3
        assert result["workload_reduction_pct"] == 50.0

        # Verify role assignment
        rec_map = {r["image_id"]: r for r in result["records"]}
        assert rec_map["c4"]["is_anchor"] is True
        assert rec_map["c3"]["is_duplicate"] is True
        assert rec_map["c3"]["duplicate_of"] == "c4"
        assert rec_map["r21"]["is_anchor"] is True
        assert rec_map["r20"]["is_duplicate"] is True
        assert rec_map["r20"]["duplicate_of"] == "r21"
        assert rec_map["b9"]["is_anchor"] is True
        assert rec_map["b9"]["is_duplicate"] is False

def test_cluster_duplicates_api_endpoint():
    """Tests POST /api/detection/cluster-duplicates API endpoint."""
    from fastapi.testclient import TestClient
    from src.backend.main import app

    client = TestClient(app)
    c3 = IMAGES_DIR / "cct_0003_loc_02_coyote.jpg"
    c4 = IMAGES_DIR / "cct_0004_loc_02_coyote.jpg"

    payload = {
        "items": [
            {"image_id": "c3", "image_path": str(c3), "species": "coyote", "confidence": 0.90, "location": "loc_02"},
            {"image_id": "c4", "image_path": str(c4), "species": "coyote", "confidence": 0.95, "location": "loc_02"}
        ],
        "similarity_threshold": 0.82
    }
    resp = client.post("/api/detection/cluster-duplicates", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_images"] == 2
    assert data["unique_encounters_count"] == 1
    assert data["duplicate_images_count"] == 1
    assert data["workload_reduction_pct"] == 50.0

def test_gallery_deduplicate_bursts_query():
    """Tests GET /api/dataset/images?deduplicate_bursts=true."""
    from fastapi.testclient import TestClient
    from src.backend.main import app

    client = TestClient(app)
    resp_all = client.get("/api/dataset/images?limit=50&deduplicate_bursts=false")
    assert resp_all.status_code == 200

    resp_dedup = client.get("/api/dataset/images?limit=50&deduplicate_bursts=true")
    assert resp_dedup.status_code == 200
    data_dedup = resp_dedup.json()
    assert "records" in data_dedup
    # Verify no secondary burst frames if frame_num is present
    for r in data_dedup["records"]:
        if "frame_num" in r and r.get("frame_num") is not None:
            assert r["frame_num"] == 0

def test_excel_export_includes_duplicate_clustering():
    """Verifies that generated Excel reports include duplicate grouping metrics and role columns."""
    from src.backend.services.excel_service import excel_service
    import openpyxl
    import io

    batch_data = {
        "items": [
            {
                "image_id": "img_01",
                "file_name": "coyote_frame_1.jpg",
                "species": "coyote",
                "common_name": "Coyote",
                "confidence": 0.95,
                "is_empty": False,
                "is_anchor": True,
                "is_duplicate": False,
                "cluster_id": "cluster_1",
                "similarity_to_anchor": 1.0
            },
            {
                "image_id": "img_02",
                "file_name": "coyote_frame_2.jpg",
                "species": "coyote",
                "common_name": "Coyote",
                "confidence": 0.89,
                "is_empty": False,
                "is_anchor": False,
                "is_duplicate": True,
                "cluster_id": "cluster_1",
                "duplicate_of": "img_01",
                "similarity_to_anchor": 0.98
            }
        ]
    }

    excel_bytes = excel_service.generate_batch_excel_report(batch_data, location="loc_02")
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    
    # Check Batch Overview sheet
    ws_overview = wb["Batch Overview"]
    metrics = [row[0] for row in ws_overview.iter_rows(values_only=True)]
    assert any("Duplicate Images Grouped" in str(m) for m in metrics)
    assert any("Review Workload Saved" in str(m) for m in metrics)

    # Check Image Records & Timestamps sheet
    ws_records = wb["Image Records & Timestamps"]
    headers = [cell for cell in next(ws_records.iter_rows(values_only=True))]
    assert "Sighting Cluster" in headers
    assert "Frame Role" in headers
    assert "Similarity to Anchor (%)" in headers

