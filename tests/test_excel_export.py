"""
Unit Tests for Excel Export Service & Batch Detections
Verifies:
1. Excel file creation with .xlsx multi-sheet layout.
2. Accurate counts ("how many are there" per species and overall).
3. Inclusion of timestamp on both batch overview and individual image records.
4. FastAPI endpoints for batch Excel export (POST and GET).
"""

import io
import pytest
from datetime import datetime
import openpyxl
from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.services.excel_service import excel_service

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_batch_data():
    return {
        "timestamp": "2026-10-31 12:00:00",
        "location": "loc_03",
        "total_processed": 4,
        "items": [
            {
                "file_name": "cam1_fox_01.jpg",
                "species": "gray_fox",
                "common_name": "Gray Fox",
                "is_empty": False,
                "confidence": 0.88,
                "location": "loc_03",
                "timestamp": "2026-10-31 11:58:10",
                "datetime": "2026-10-31 11:58:10",
                "is_night": True,
                "uncertainty_flags": ["Night Vision (CLAHE + Bilateral)", "High Certainty"],
                "bounding_box": {"ymin": 0.2, "xmin": 0.2, "ymax": 0.8, "xmax": 0.8}
            },
            {
                "file_name": "cam1_fox_02.jpg",
                "species": "gray_fox",
                "common_name": "Gray Fox",
                "is_empty": False,
                "confidence": 0.84,
                "location": "loc_03",
                "timestamp": "2026-10-31 11:58:13",
                "datetime": "2026-10-31 11:58:13",
                "is_night": True,
                "uncertainty_flags": ["Night Vision (CLAHE + Bilateral)"],
                "bounding_box": {"ymin": 0.2, "xmin": 0.2, "ymax": 0.8, "xmax": 0.8}
            },
            {
                "file_name": "cam1_deer_01.jpg",
                "species": "mule_deer",
                "common_name": "Mule Deer",
                "is_empty": False,
                "confidence": 0.92,
                "location": "loc_03",
                "timestamp": "2026-10-31 11:59:00",
                "datetime": "2026-10-31 11:59:00",
                "is_night": False,
                "uncertainty_flags": ["High Certainty"],
                "bounding_box": {"ymin": 0.1, "xmin": 0.1, "ymax": 0.9, "xmax": 0.9}
            },
            {
                "file_name": "cam1_empty_01.jpg",
                "species": "empty",
                "common_name": "Empty Frame",
                "is_empty": True,
                "confidence": 0.99,
                "location": "loc_03",
                "timestamp": "2026-10-31 11:59:30",
                "datetime": "2026-10-31 11:59:30",
                "is_night": False,
                "empty_reason": "Windblown vegetation without wildlife",
                "uncertainty_flags": ["Empty Frame Filtered"]
            }
        ]
    }

def test_excel_service_generation_and_counts(sample_batch_data):
    """Verifies that Excel workbook generates correctly with timestamps and counts."""
    excel_bytes = excel_service.generate_batch_excel_report(
        batch_data=sample_batch_data,
        location="loc_03",
        export_time="2026-10-31 12:00:00"
    )

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 2000

    # Load workbook and inspect contents
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    assert "Batch Overview" in wb.sheetnames
    assert "Species Counts" in wb.sheetnames
    assert "Image Records & Timestamps" in wb.sheetnames

    # Check Overview tab for timestamp and counts
    ws_overview = wb["Batch Overview"]
    overview_dict = {row[0]: row[1] for row in ws_overview.iter_rows(values_only=True) if row[0]}
    assert overview_dict["Batch Export Timestamp"] == "2026-10-31 12:00:00"
    assert overview_dict["Total Images Uploaded"] == 4
    assert overview_dict["Animals Detected (Count)"] == 3
    assert overview_dict["Empty Frames Filtered (Count)"] == 1
    assert overview_dict["Camera Station / Location"] == "loc_03"

    # Check Species Counts tab ("how many are there")
    ws_species = wb["Species Counts"]
    species_rows = list(ws_species.iter_rows(values_only=True))[1:]  # skip header
    species_counts = {r[0]: r[1] for r in species_rows}
    assert species_counts["Gray Fox"] == 2  # exactly 2 foxes
    assert species_counts["Mule Deer"] == 1  # exactly 1 deer

    # Check Detailed Records & Timestamps tab
    ws_details = wb["Image Records & Timestamps"]
    detail_rows = list(ws_details.iter_rows(values_only=True))
    assert len(detail_rows) == 5  # header + 4 rows
    headers = detail_rows[0]
    assert "Timestamp" in headers
    assert "File Name" in headers
    assert "Detection Status" in headers

    # Verify timestamp in individual record
    row1 = detail_rows[1]
    timestamp_idx = headers.index("Timestamp")
    assert row1[timestamp_idx] == "2026-10-31 11:58:10"

def test_api_export_batch_excel_post(client, sample_batch_data):
    """Verifies POST /api/detection/export-batch-excel returns valid downloadable .xlsx."""
    res = client.post("/api/detection/export-batch-excel", json={
        "items": sample_batch_data["items"],
        "location": "loc_03",
        "timestamp": "2026-10-31 12:00:00"
    })

    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res.headers["content-type"]
    assert "wildlife_batch_summary_" in res.headers["content-disposition"]
    assert ".xlsx" in res.headers["content-disposition"]

    # Verify readable as Excel
    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    assert len(wb.sheetnames) == 3

def test_api_predict_batch_returns_timestamp_and_counts(client):
    """Verifies /api/detection/predict-batch includes timestamps and detection counts."""
    # Create simple dummy image bytes
    from PIL import Image
    buf1 = io.BytesIO()
    Image.new("RGB", (64, 64), (100, 150, 100)).save(buf1, "JPEG")
    buf1.seek(0)

    buf2 = io.BytesIO()
    Image.new("RGB", (64, 64), (30, 30, 30)).save(buf2, "JPEG")
    buf2.seek(0)

    files = [
        ("files", ("test1.jpg", buf1.getvalue(), "image/jpeg")),
        ("files", ("test2.jpg", buf2.getvalue(), "image/jpeg"))
    ]

    res = client.post("/api/detection/predict-batch", files=files, data={"location": "loc_02"})
    assert res.status_code == 200
    data = res.json()

    assert "timestamp" in data
    assert "total_processed" in data
    assert "animals_detected_count" in data
    assert data["total_processed"] == 2
    assert len(data["items"]) == 2
    assert "timestamp" in data["items"][0]
    assert "datetime" in data["items"][0]
