"""
Unit Tests for Animal Detection & Empty Frame Filtering
"""

import pytest
from PIL import Image, ImageDraw
from src.backend.models.detector import AnimalDetector

@pytest.fixture
def detector():
    return AnimalDetector(confidence_threshold=0.45)

def test_sensor_properties_daylight(detector):
    """Verifies sensor properties extraction on a daylight image."""
    img = Image.new("RGB", (320, 240), color=(180, 160, 120))
    props = detector.analyze_image_properties(img)
    
    assert props["width"] == 320
    assert props["height"] == 240
    assert props["is_night"] is False
    assert props["is_ir_monochrome"] is False
    assert props["luminance"] > 100

def test_sensor_properties_night_ir(detector):
    """Verifies sensor properties extraction on monochrome IR nighttime frame."""
    # Charcoal monochrome IR
    img = Image.new("RGB", (320, 240), color=(40, 40, 40))
    props = detector.analyze_image_properties(img)
    
    assert props["is_night"] is True
    assert props["is_ir_monochrome"] is True
    assert props["luminance"] < 65

def test_detect_empty_uniform_image(detector):
    """Verifies that flat uniform image without animal is filtered as empty."""
    img = Image.new("RGB", (256, 192), color=(128, 128, 128))
    result = detector.detect(img)
    
    assert result["is_empty"] is True
    assert result["has_animal"] is False
    assert result["confidence"] < 0.45
    assert result["empty_reason"] is not None
    assert result["bounding_box"]["ymin"] == 0.0

def test_detect_image_with_salient_subject(detector):
    """Verifies that an image with a high contrast subject is detected."""
    img = Image.new("RGB", (256, 192), color=(40, 40, 40))
    draw = ImageDraw.Draw(img)
    # Draw high-contrast subject in center
    draw.ellipse([80, 60, 180, 140], fill=(230, 230, 230))
    
    result = detector.detect(img)
    assert result["has_animal"] is True
    assert result["is_empty"] is False
    assert result["confidence"] >= 0.45
    bbox = result["bounding_box"]
    assert 0.0 <= bbox["ymin"] < bbox["ymax"] <= 1.0
    assert 0.0 <= bbox["xmin"] < bbox["xmax"] <= 1.0

def test_detect_night_infrared_frame(detector):
    """Verifies that low-light / monochrome IR animal scene is detected with night properties."""
    img = Image.new("RGB", (256, 192), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    # Night IR illuminated animal
    draw.ellipse([70, 50, 170, 130], fill=(110, 110, 110))
    
    result = detector.detect(img)
    assert result["sensor_props"]["is_night"] is True
    assert result["has_animal"] is True
    assert result["confidence"] >= 0.45
