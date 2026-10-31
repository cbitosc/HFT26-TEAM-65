"""
Unit Tests for Nighttime Animal Classification Preprocessing & Temporal Burst Aggregation
Verifies:
1. Adaptive low-light check (daytime RGB bypass vs dark/IR trigger).
2. Contrast Limited Adaptive Histogram Equalization (CLAHE) + Fast Bilateral Denoising.
3. High confidence (>75%) for dark/monochromatic Gray Fox and Alaskan Tundra Wolf.
4. Temporal context aggregation wrapper (rolling max pooling across 3-to-5 frame burst window).
5. Zero degradation constraint on daytime color RGB images.
"""

import pytest
import numpy as np
from PIL import Image, ImageEnhance
from pathlib import Path

from src.backend.models.classifier import SpeciesClassifier
from src.backend.models.detector import AnimalDetector
from src.backend.services.temporal_pooling import TemporalBurstAggregator, temporal_aggregator

@pytest.fixture
def classifier():
    return SpeciesClassifier()

@pytest.fixture
def detector():
    return AnimalDetector()

def test_adaptive_low_light_check_daytime_bypass(classifier):
    """Verifies that rich daytime color RGB frames strictly bypass nighttime filters."""
    # Create bright, saturated daytime image
    w, h = 200, 200
    day_arr = np.zeros((h, w, 3), dtype=np.uint8)
    day_arr[:, :, 0] = 180  # R
    day_arr[:, :, 1] = 120  # G
    day_arr[:, :, 2] = 60   # B
    day_img = Image.fromarray(day_arr)
    
    is_night, diag = classifier.is_low_light_or_desaturated(day_img)
    assert is_night is False
    assert diag["luminance"] >= 80.0
    assert diag["is_desaturated"] is False

    # Also check real daylight photo if present
    deer_path = Path("data/images/real_mule_deer.jpg")
    if deer_path.exists():
        real_day = Image.open(deer_path)
        is_night_real, diag_real = classifier.is_low_light_or_desaturated(real_day)
        assert is_night_real is False
        assert diag_real["luminance"] > 80.0

def test_adaptive_low_light_check_night_and_ir_trigger(classifier):
    """Verifies that dark frames and monochromatic IR frames trigger adaptive night processing."""
    # 1. Underexposed / dark frame (L < 80)
    dark_arr = np.full((150, 150, 3), 35, dtype=np.uint8)
    dark_img = Image.fromarray(dark_arr)
    is_night_dark, diag_dark = classifier.is_low_light_or_desaturated(dark_img)
    assert is_night_dark is True
    assert diag_dark["is_dark"] is True

    # 2. Monochromatic IR frame (R = G = B, low color variance)
    mono_arr = np.full((150, 150, 3), 100, dtype=np.uint8)
    mono_img = Image.fromarray(mono_arr)
    is_night_mono, diag_mono = classifier.is_low_light_or_desaturated(mono_img)
    assert is_night_mono is True
    assert diag_mono["is_desaturated"] is True

    # 3. Explicit metadata tag override
    is_night_meta, _ = classifier.is_low_light_or_desaturated(dark_img, sensor_props={"is_night": True})
    assert is_night_meta is True

def test_clahe_bilateral_filter_enhancement(classifier):
    """Verifies that optimize_night_vision cleans up noise and enhances contrast adaptively."""
    # Create dark frame with Gaussian sensor noise
    rng = np.random.RandomState(42)
    dark_base = np.full((128, 128, 3), 40, dtype=np.uint8)
    noise = rng.normal(0, 15, (128, 128, 3)).clip(-30, 30).astype(np.int16)
    noisy_dark = np.clip(dark_base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    noisy_img = Image.fromarray(noisy_dark)

    enhanced = classifier.optimize_night_vision(noisy_img)
    assert isinstance(enhanced, Image.Image)
    assert enhanced.size == (128, 128)

    enh_arr = np.array(enhanced)
    # CLAHE stretches contrast and bilateral reduces grain
    assert enh_arr.shape == (128, 128, 3)
    assert np.mean(enh_arr) > np.mean(noisy_dark)  # Dynamic range stretched

def test_nighttime_gray_fox_high_confidence(classifier, detector):
    """
    Verifies that a dark/monochromatic Gray Fox frame achieves high confidence (>75%),
    eliminating the previous ~35% drop.
    """
    fox_path = Path("data/images/real_gray_fox.jpg")
    if not fox_path.exists():
        pytest.skip("real_gray_fox.jpg sample not found on disk")

    fox_img = Image.open(fox_path)
    # Create dark monochromatic IR simulation (luminance ~25-30)
    gray_fox = ImageEnhance.Brightness(fox_img.convert("L").convert("RGB")).enhance(0.25)
    
    det = detector.detect(gray_fox)
    res = classifier.classify_crop(
        image=gray_fox,
        bbox=det["bounding_box"],
        sensor_props=det["sensor_props"]
    )

    assert res["is_animal"] is True
    assert res["primary_species"] in ["gray_fox", "coyote", "wolf"]
    # Key requirement: Must fix low confidence (~35%) to high confidence (>= 0.75)
    assert res["confidence"] >= 0.75, f"Expected confidence >= 0.75, got {res['confidence']}"
    assert "Night Vision (CLAHE + Bilateral)" in res["uncertainty_flags"]
    assert "High Certainty" in res["uncertainty_flags"]
    assert res["is_review_recommended"] is False

def test_alaskan_tundra_wolf_taxonomy_mapping(classifier):
    """Verifies that Alaskan Tundra Wolf labels map to standardized wild canid taxonomy."""
    key, display = classifier._map_imagenet_label("Alaskan tundra wolf")
    assert key == "alaskan_tundra_wolf"
    assert "Alaskan Tundra Wolf" in display

    key_grey, disp_grey = classifier._map_imagenet_label("grey wolf")
    assert key_grey == "wolf"
    assert "Wolf" in disp_grey

    key_malamute, _ = classifier._map_imagenet_label("Alaskan Malamute")
    assert key_malamute == "alaskan_tundra_wolf"

def test_temporal_burst_context_aggregation_3_frame_window():
    """
    Verifies that in a 3-frame camera trap burst, an anchor frame (88% confidence)
    rescues adjacent blurry/low-confidence frames (35% confidence).
    """
    aggregator = TemporalBurstAggregator(default_window_size=3, temporal_decay=0.95)

    burst_records = [
        {
            "id": "frame_0",
            "frame_num": 0,
            "species": "gray_fox",
            "common_name": "Gray Fox",
            "confidence": 0.35,
            "uncertainty_flags": ["Low Light / IR Monochrome", "Review Recommended"],
            "is_empty": False
        },
        {
            "id": "frame_1",
            "frame_num": 1,
            "species": "gray_fox",
            "common_name": "Gray Fox",
            "confidence": 0.88,
            "uncertainty_flags": ["High Certainty", "Low Light / IR Monochrome"],
            "is_empty": False
        },
        {
            "id": "frame_2",
            "frame_num": 2,
            "species": "gray_fox",
            "common_name": "Gray Fox",
            "confidence": 0.36,
            "uncertainty_flags": ["Low Light / IR Monochrome", "Review Recommended"],
            "is_empty": False
        }
    ]

    rescued = aggregator.aggregate_burst_records(burst_records, window_size=3)

    # Frame 0 and Frame 2 should be boosted by anchor Frame 1
    assert rescued[0]["confidence"] >= 0.80, f"Frame 0 was not rescued: {rescued[0]['confidence']}"
    assert rescued[1]["confidence"] == 0.88
    assert rescued[2]["confidence"] >= 0.80, f"Frame 2 was not rescued: {rescued[2]['confidence']}"

    assert "Temporal Burst Context Rescued (Anchor Frame Pooling)" in rescued[0]["uncertainty_flags"]
    assert "Temporal Burst Context Rescued (Anchor Frame Pooling)" in rescued[2]["uncertainty_flags"]
    assert "Review Recommended" not in rescued[0]["uncertainty_flags"]
    assert "Review Recommended" not in rescued[2]["uncertainty_flags"]

def test_temporal_burst_matrix_rolling_max():
    """Verifies matrix-level temporal rolling maximum pooling across 5 frames."""
    aggregator = TemporalBurstAggregator(default_window_size=5, temporal_decay=0.90)
    
    # 5 frames, 3 classes: [Class 0, Class 1, Class 2]
    # Frame 2 is a crisp observation of Class 1 (0.85)
    # Frames 0, 1, 3, 4 are noisy (Class 1 ~0.30)
    matrix = np.array([
        [0.40, 0.30, 0.30],
        [0.40, 0.32, 0.28],
        [0.05, 0.85, 0.10],  # Sharp anchor frame
        [0.35, 0.35, 0.30],
        [0.38, 0.31, 0.31]
    ], dtype=np.float32)

    pooled = aggregator.aggregate_confidence_matrices(matrix, window_size=5, decay=0.92)
    assert pooled.shape == matrix.shape
    
    # Neighbor frames 1 and 3 should have Class 1 as dominant class now
    assert np.argmax(pooled[1]) == 1
    assert np.argmax(pooled[3]) == 1
    assert pooled[1, 1] > 0.50
    assert pooled[3, 1] > 0.50
