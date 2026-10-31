"""
Featherless AI / LLM Integration API Endpoints
Handles natural-language ecological report synthesis, detection explainability,
and model configuration.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from src.backend.services.featherless_service import featherless_service
from src.backend.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/featherless", tags=["Featherless AI / LLM"])

class SummaryRequest(BaseModel):
    species: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    custom_instructions: Optional[str] = None

class ExplainRequest(BaseModel):
    species: str
    confidence: float
    uncertainty_flags: Optional[List[str]] = None
    bbox: Optional[Dict[str, float]] = None
    is_night: Optional[bool] = False

class ConfigRequest(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None

@router.get("/status")
async def get_featherless_status():
    """Returns Featherless AI configuration status and active mode."""
    return featherless_service.get_status()

@router.post("/config")
async def update_featherless_config(config: ConfigRequest):
    """Dynamically updates the Featherless API key and model selection."""
    featherless_service.update_config(api_key=config.api_key, model=config.model)
    return {
        "status": "updated",
        "current": featherless_service.get_status()
    }

@router.post("/summary")
async def generate_summary(req: SummaryRequest):
    """
    Synthesizes a comprehensive natural-language ecological report from current data.
    """
    metrics = analytics_service.get_overview_metrics(
        species_filter=req.species,
        location_filter=req.locations
    )
    temporal = analytics_service.get_temporal_analytics(
        species_filter=req.species,
        location_filter=req.locations
    )
    spatial = analytics_service.get_spatial_analytics(
        species_filter=req.species
    )

    return await featherless_service.generate_ecological_summary(
        metrics=metrics,
        temporal_data=temporal,
        spatial_data=spatial,
        custom_instructions=req.custom_instructions
    )

class LLMClassifyRequest(BaseModel):
    image_data: str
    is_night_mode: Optional[bool] = False

@router.post("/explain")
async def explain_detection(req: ExplainRequest):
    """
    Generates a morphological and sensor explanation for an individual detection.
    """
    return await featherless_service.explain_detection(
        species=req.species,
        confidence=req.confidence,
        uncertainty_flags=req.uncertainty_flags or [],
        bbox=req.bbox,
        is_night=req.is_night or False
    )

@router.post("/classify")
async def classify_with_llm(req: LLMClassifyRequest):
    """
    Dynamic routing LLM classification with zero-temperature infrared night vision override.
    """
    return await featherless_service.get_llm_classification(
        image_data=req.image_data,
        is_night_mode=req.is_night_mode or False
    )
