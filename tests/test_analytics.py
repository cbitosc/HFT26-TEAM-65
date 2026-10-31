"""
Unit Tests for Ecological Analytics & Biodiversity Indices
"""

import pytest
from src.backend.services.analytics_service import AnalyticsService

@pytest.fixture
def analytics():
    return AnalyticsService()

def test_overview_metrics(analytics):
    """Verifies overview KPIs and biodiversity indices."""
    metrics = analytics.get_overview_metrics()
    
    assert metrics["total_images"] > 0
    assert metrics["empty_count"] > 0
    assert 35.0 <= metrics["empty_rate_pct"] <= 85.0
    assert metrics["species_richness"] >= 5
    assert metrics["shannon_diversity_index"] > 1.0
    assert 0.0 <= metrics["simpson_diversity_index"] <= 1.0
    assert 0.0 <= metrics["pielou_evenness"] <= 1.0
    assert metrics["hours_saved"] > 0.0

def test_temporal_diel_analytics(analytics):
    """Verifies 24-hour circular activity curve and diel categorization."""
    temporal = analytics.get_temporal_analytics()
    
    hourly = temporal["hourly_distribution"]
    assert len(hourly) == 24
    assert sum(h["total"] for h in hourly) == temporal["total_independent_sightings"]
    
    diel = temporal["diel_classifications"]
    assert len(diel) > 0
    for sp, info in diel.items():
        assert "category" in info
        assert info["category"] in [
            "Strictly Nocturnal",
            "Strictly Diurnal",
            "Crepuscular",
            "Cathemeral (Flexible Day/Night)"
        ]
        assert info["night_pct"] + info["day_pct"] + info["crepuscular_pct"] == pytest.approx(100.0, abs=1.5)

def test_spatial_analytics(analytics):
    """Verifies spatial camera stations and co-occurrence."""
    spatial = analytics.get_spatial_analytics()
    
    stations = spatial["stations"]
    assert len(stations) == 8
    for st in stations:
        assert st["location_id"].startswith("loc_")
        assert -180.0 <= st["lng"] <= 180.0
        assert -90.0 <= st["lat"] <= 90.0
        assert st["total_images"] >= st["empty_images"]
        
    co_occ = spatial["top_co_occurrences"]
    assert isinstance(co_occ, list)
