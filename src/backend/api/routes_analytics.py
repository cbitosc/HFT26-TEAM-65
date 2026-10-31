"""
Analytics & Ecological Telemetry API Endpoints
Provides temporal circadian curves, spatial station mapping, and biodiversity calculations.
"""

from typing import Optional, List
from fastapi import APIRouter, Query
from src.backend.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Ecological Analytics"])

@router.get("/overview")
async def get_analytics_overview(
    species: Optional[str] = Query(None, description="Comma-separated species filter"),
    locations: Optional[str] = Query(None, description="Comma-separated location IDs")
):
    """
    Returns high-level ecological KPIs:
    - Total images, empty filtering rate, hours saved
    - Species richness, Shannon-Wiener index, Simpson index, Pielou evenness
    - Review required count
    """
    sp_list = [s.strip() for s in species.split(",")] if species else None
    loc_list = [l.strip() for l in locations.split(",")] if locations else None

    return analytics_service.get_overview_metrics(
        species_filter=sp_list,
        location_filter=loc_list
    )

@router.get("/temporal")
async def get_temporal_analytics(
    species: Optional[str] = Query(None, description="Comma-separated species filter"),
    locations: Optional[str] = Query(None, description="Comma-separated location IDs")
):
    """
    Returns 24-hour circular diel activity curve, hourly breakdown,
    and nocturnal / diurnal / crepuscular classifications.
    """
    sp_list = [s.strip() for s in species.split(",")] if species else None
    loc_list = [l.strip() for l in locations.split(",")] if locations else None

    return analytics_service.get_temporal_analytics(
        species_filter=sp_list,
        location_filter=loc_list
    )

@router.get("/spatial")
async def get_spatial_analytics(
    species: Optional[str] = Query(None, description="Comma-separated species filter")
):
    """
    Returns camera station metrics, GPS coordinates, encounter rates,
    and species co-occurrence matrix.
    """
    sp_list = [s.strip() for s in species.split(",")] if species else None
    return analytics_service.get_spatial_analytics(species_filter=sp_list)
