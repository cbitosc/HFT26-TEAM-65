"""
Unit Tests for Species Classification & Uncertainty Quantification
"""

import pytest
import numpy as np
from PIL import Image
from src.backend.models.classifier import SpeciesClassifier

@pytest.fixture
def classifier():
    return SpeciesClassifier()

def test_empty_frame_classification(classifier):
    """Verifies that an image flagged empty is classified as empty with high certainty."""
    img = Image.new("RGB", (100, 100), color=(100, 100, 100))
    res = classifier.classify_crop(img, is_empty_detected=True)
    
    assert res["primary_species"] == "empty"
    assert res["confidence"] >= 0.95
    assert "High Certainty" in res["uncertainty_flags"]
    assert res["is_review_recommended"] is False

def test_entropy_calculation(classifier):
    """Verifies Shannon entropy formula."""
    # Deterministic distribution
    deterministic = np.array([1.0, 0.0, 0.0])
    assert classifier.calculate_entropy(deterministic) < 0.01

    # Uniform distribution (maximum uncertainty)
    uniform = np.array([0.3333, 0.3333, 0.3334])
    entropy_uniform = classifier.calculate_entropy(uniform)
    assert entropy_uniform > 1.0

def test_species_classification_with_sensor_props(classifier):
    """Verifies that species classification returns valid classes and probabilities."""
    img = Image.new("RGB", (200, 150), color=(50, 50, 50))
    bbox = {"ymin": 0.2, "xmin": 0.2, "ymax": 0.8, "xmax": 0.8}
    sensor_props = {"is_night": True, "is_ir_monochrome": True, "edge_energy": 7.5}
    
    res = classifier.classify_crop(
        image=img,
        bbox=bbox,
        is_empty_detected=False,
        sensor_props=sensor_props
    )
    
    assert res["primary_species"] in classifier.CLASSES
    assert 0.0 <= res["confidence"] <= 1.0
    assert 0.0 <= res["uncertainty_score"] <= 1.0
    assert len(res["top_predictions"]) >= 3
    assert res["top_predictions"][0]["confidence"] >= res["top_predictions"][1]["confidence"]
    assert "Low Light / IR Monochrome" in res["uncertainty_flags"]

def test_non_animal_detection(classifier):
    """Verifies that non-animal images (e.g. websites, vehicles, landscape) return Animal Not Detected."""
    from pathlib import Path
    website_img_path = Path("docs/12345.jpeg")
    if website_img_path.exists():
        img = Image.open(website_img_path)
        res = classifier.classify_crop(img)
        assert res["is_animal"] is False
        assert res["common_name"] == "Animal Not Detected"
        assert res["primary_species"] == "empty"
        assert "Animal Not Detected" in res["uncertainty_flags"]

    animal_img_path = Path("data/images/real_elephant.jpg")
    if animal_img_path.exists():
        img_animal = Image.open(animal_img_path)
        res_animal = classifier.classify_crop(img_animal)
        assert res_animal["is_animal"] is True
        assert "Elephant" in res_animal["common_name"]
        assert res_animal["primary_species"] == "elephant"

def test_night_vision_optimization(classifier):
    """Verifies that dark / nighttime frames activate night vision and preserve wildlife classification."""
    from PIL import ImageEnhance
    from pathlib import Path
    img_path = Path("data/images/real_bobcat.jpg")
    if img_path.exists():
        img = Image.open(img_path)
        # Create dark night version (brightness 0.25)
        dark_img = ImageEnhance.Brightness(img).enhance(0.25)
        sensor_props = {"is_night": True, "is_ir_monochrome": False, "edge_energy": 5.0}
        
        res = classifier.classify_crop(dark_img, sensor_props=sensor_props)
        assert res["is_animal"] is True
        assert "Night Vision (IR Enhanced)" in res["uncertainty_flags"]
        assert res["is_night"] is True
        assert res["night_mode_active"] is True
