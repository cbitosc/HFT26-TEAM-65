"""
Unit Tests for Featherless AI Integration & Fallback Ecological Synthesizer
"""

import asyncio
import pytest
from src.backend.services.featherless_service import FeatherlessService

@pytest.fixture
def featherless():
    return FeatherlessService()

def test_featherless_status(featherless):
    """Verifies service configuration status."""
    status = featherless.get_status()
    assert "provider" in status
    assert "model" in status
    assert "mode" in status

def test_fallback_ecological_summary(featherless):
    """Verifies automated natural-language summary synthesis in fallback mode."""
    metrics = {
        "total_images": 500,
        "empty_count": 340,
        "empty_rate_pct": 68.0,
        "independent_events": 95,
        "species_richness": 8,
        "shannon_diversity_index": 1.84,
        "simpson_diversity_index": 0.81,
        "hours_saved": 42.5,
        "review_required_count": 14,
        "species_distribution": {"coyote": 30, "mule_deer": 25, "bobcat": 15}
    }
    temporal = {
        "diel_classifications": {
            "coyote": {"category": "Strictly Nocturnal"},
            "mule_deer": {"category": "Crepuscular"}
        }
    }
    spatial = {
        "stations": [
            {"name": "Riparian Arroyo", "wildlife_events": 40, "dominant_species": "coyote"}
        ]
    }

    res = asyncio.run(featherless.generate_ecological_summary(
        metrics, temporal, spatial, custom_instructions="Test prompt"
    ))
    
    assert res is not None
    assert "summary_markdown" in res
    assert len(res["summary_markdown"]) > 200
    assert "Executive Wildlife Monitoring" in res["summary_markdown"]
    assert "Shannon-Wiener" in res["summary_markdown"]

def test_explain_detection(featherless):
    """Verifies morphological and sensor explanation for a specific detection."""
    explanation = asyncio.run(featherless.explain_detection(
        species="bobcat",
        confidence=0.92,
        uncertainty_flags=["Low Light / IR Monochrome", "High Certainty"],
        is_night=True
    ))
    
    assert explanation["species"] == "bobcat"
    assert "Bobcat" in explanation["explanation"]
    assert "ear tufts" in explanation["explanation"] or "bobbed tail" in explanation["explanation"]
    assert "CRITICAL OVERRIDE: NIGHT VISION ACTIVE" in explanation["explanation"]
    assert explanation["is_night"] is True

def test_dynamic_night_routing_classification(featherless):
    """Verifies dynamic system prompt and zero temperature enforcement for night mode."""
    # 1. Daytime routing
    day_res = asyncio.run(featherless.get_llm_classification(
        image_data="data:image/jpeg;base64,...",
        is_night_mode=False
    ))
    assert day_res["temperature"] == 0.2
    assert "CRITICAL OVERRIDE: NIGHT VISION ACTIVE" not in day_res["system_prompt"]
    assert day_res["is_night_mode"] is False

    # 2. Nighttime routing
    night_res = asyncio.run(featherless.get_llm_classification(
        image_data="data:image/jpeg;base64,...",
        is_night_mode=True
    ))
    assert night_res["temperature"] == 0.0
    assert "CRITICAL OVERRIDE: NIGHT VISION ACTIVE" in night_res["system_prompt"]
    assert "deer-like silhouette, large upright ears, and thin legs, it is a Deer, NOT a dog" in night_res["system_prompt"]
    assert night_res["is_night_mode"] is True
    assert night_res["predicted_override"] == "mule_deer"
