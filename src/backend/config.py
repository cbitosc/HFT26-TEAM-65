"""
Application Configuration for Wildlife Monitoring & Camera-Trap Analytics System
All data, uploads, and assets are hosted under the project workspace on D: drive.
"""

import os
from pathlib import Path
from pydantic import BaseModel

# Base Directory: strictly on D: drive
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
UPLOADS_DIR = DATA_DIR / "uploads"
BENCHMARK_FILE = DATA_DIR / "benchmark_cct_sample.json"
CALTECH_DB_FILE = DATA_DIR / "caltech_243k.sqlite"
CALTECH_ZIP_FILE = DATA_DIR / "caltech_camera_traps.json.zip"

# Ensure runtime directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "AI-Powered Wildlife Monitoring & Camera-Trap Analytics System"
    app_version: str = "2.0.0"
    team_name: str = "The Chosen One"
    team_id: str = "TEAM-65"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Model thresholds
    animal_detection_threshold: float = float(os.getenv("DETECTION_THRESHOLD", "0.45"))
    uncertainty_entropy_threshold: float = float(os.getenv("UNCERTAINTY_THRESHOLD", "1.15"))
    burst_time_window_seconds: int = int(os.getenv("BURST_WINDOW_SEC", "60"))
    
    # Featherless AI Settings
    featherless_api_key: str = os.getenv("FEATHERLESS_API_KEY", "")
    featherless_base_url: str = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
    featherless_model: str = os.getenv("FEATHERLESS_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
    
    # Supported Caltech Camera Traps species taxonomy
    species_taxonomy: dict = {
        0: {"key": "empty", "common": "Empty Frame", "scientific": "N/A", "trophic": "None"},
        1: {"key": "coyote", "common": "Coyote", "scientific": "Canis latrans", "trophic": "Mesopredator"},
        2: {"key": "bobcat", "common": "Bobcat", "scientific": "Lynx rufus", "trophic": "Carnivore"},
        3: {"key": "mule_deer", "common": "Mule Deer", "scientific": "Odocoileus hemionus", "trophic": "Herbivore"},
        4: {"key": "opossum", "common": "Virginia Opossum", "scientific": "Didelphis virginiana", "trophic": "Omnivore"},
        5: {"key": "raccoon", "common": "Raccoon", "scientific": "Procyon lotor", "trophic": "Omnivore"},
        6: {"key": "mountain_lion", "common": "Mountain Lion", "scientific": "Puma concolor", "trophic": "Apex Predator"},
        7: {"key": "gray_fox", "common": "Gray Fox", "scientific": "Urocyon cinereoargenteus", "trophic": "Mesopredator"},
        8: {"key": "striped_skunk", "common": "Striped Skunk", "scientific": "Mephitis mephitis", "trophic": "Omnivore"},
        9: {"key": "cottontail_rabbit", "common": "Cottontail Rabbit", "scientific": "Sylvilagus audubonii", "trophic": "Small Herbivore"},
        10: {"key": "bird", "common": "Avian Fauna", "scientific": "Aves spp.", "trophic": "Diverse"},
        11: {"key": "rodent", "common": "Woodrat / Squirrel", "scientific": "Rodentia spp.", "trophic": "Small Herbivore"},
        12: {"key": "domestic_dog", "common": "Domestic Dog", "scientific": "Canis lupus familiaris", "trophic": "Anthropogenic"},
        13: {"key": "domestic_cat", "common": "Domestic Cat", "scientific": "Felis catus", "trophic": "Anthropogenic"},
        14: {"key": "alaskan_tundra_wolf", "common": "Alaskan Tundra Wolf", "scientific": "Canis lupus albus", "trophic": "Apex Predator"},
        15: {"key": "wolf", "common": "Wolf", "scientific": "Canis lupus", "trophic": "Apex Predator"}
    }

settings = Settings()
