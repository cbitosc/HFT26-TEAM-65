"""
Unit Tests for Caltech Camera Traps Dataset Service & Burst Deduplication
"""

import pytest
from src.backend.services.dataset_service import DatasetService

@pytest.fixture
def service():
    return DatasetService()

def test_dataset_coco_schema(service):
    """Verifies that the dataset follows the COCO Camera Traps format."""
    ds = service.get_dataset()
    
    assert "info" in ds
    assert "locations" in ds
    assert "categories" in ds
    assert "images" in ds
    assert "annotations" in ds
    
    assert len(ds["images"]) > 50
    assert len(ds["annotations"]) > 50

    sample_img = ds["images"][0]
    assert "id" in sample_img
    assert "location" in sample_img
    assert "datetime" in sample_img
    assert "seq_id" in sample_img

def test_query_records_filters(service):
    """Verifies filtering by species and location."""
    # Filter by specific species
    res_coyote = service.query_records(species=["coyote"], include_empty=False)
    for rec in res_coyote["records"]:
        assert rec["species"] == "coyote"
        assert rec["is_empty"] is False

    # Filter excluding empty
    res_no_empty = service.query_records(include_empty=False)
    for rec in res_no_empty["records"]:
        assert rec["is_empty"] is False

def test_burst_sequence_deduplication(service):
    """Verifies that burst frames are deduplicated into Independent Sighting Events."""
    sample_records = [
        {"seq_id": "seq_01", "location": "loc_01", "species": "coyote", "frame_num": 0},
        {"seq_id": "seq_01", "location": "loc_01", "species": "coyote", "frame_num": 1},
        {"seq_id": "seq_01", "location": "loc_01", "species": "coyote", "frame_num": 2},
        {"seq_id": "seq_02", "location": "loc_02", "species": "bobcat", "frame_num": 0},
    ]
    
    independent = service.deduplicate_burst_sequences(sample_records)
    assert len(independent) == 2
    assert independent[0]["seq_id"] == "seq_01"
    assert independent[1]["seq_id"] == "seq_02"
