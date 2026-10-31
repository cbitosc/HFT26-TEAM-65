# 📡 REST API Specification

**Project:** AI-Powered Wildlife Monitoring & Camera-Trap Analytics System  
**Base URL:** `http://127.0.0.1:8000/api`  
**Interactive Docs:** `http://127.0.0.1:8000/docs` (Swagger UI) & `/redoc`

---

## 1. Overview

The REST API provides modular, high-throughput endpoints to:
1. Ingest camera-trap images and execute detection + species classification.
2. Filter empty vs animal frames with threshold controls.
3. Compute spatial, temporal, and diel activity patterns.
4. Interface with Featherless AI for ecological report generation and visual detection rationale.
5. Export survey findings in standard JSON and CSV formats.

---

## 2. Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check, system status, and environment diagnostics |
| `GET` | `/api/dataset/summary` | Caltech Camera Traps dataset summary, counts, and stations |
| `GET` | `/api/dataset/images` | Paginated query of camera-trap records with filter matrix (including `alerts_only`) |
| `POST` | `/api/detection/predict-image` | Upload single image for real-time animal detection, species classification & threat alerts |
| `POST` | `/api/detection/predict-batch` | Multi-image batch inference with burst sequence clustering & alert summarization |
| `GET` | `/api/detection/alerts` | Query rare and dangerous wildlife detections with threat levels and ranger safety advisories |
| `POST` | `/api/detection/export-batch-excel` | Export camera-trap batch detections to multi-tab Excel (.xlsx) report with threat alerts |
| `GET` | `/api/analytics/overview` | Overall ecological metrics: species count, empty reduction %, Shannon index |
| `GET` | `/api/analytics/temporal` | 24-hour diel activity curve, diurnal/nocturnal breakdown, hourly sightings |
| `GET` | `/api/analytics/spatial` | Camera trap station metrics, location coordinates, species distribution |
| `GET` | `/api/analytics/species-distribution` | Species frequency and confidence histogram |
| `POST` | `/api/featherless/summary` | Featherless AI natural-language ecological report generator |
| `POST` | `/api/featherless/explain` | Featherless AI detection rationale and morphological explanation |
| `GET` | `/api/featherless/status` | Featherless AI configuration status, current model, and fallback mode |

---

## 3. Detailed Endpoint Specifications

### 3.1. `POST /api/detection/predict-image`
Uploads an image file to detect animals, classify species, quantify prediction uncertainty, and trigger real-time rare/dangerous wildlife alerts.

#### Request:
- Content-Type: `multipart/form-data`
- Form Parameters:
  - `file`: Image file (JPEG, PNG)
  - `location`: (Optional) Camera station ID (e.g., `loc_03`)
  - `datetime`: (Optional) ISO timestamp (e.g., `2024-06-14T22:15:30`)
  - `confidence_threshold`: (Optional, default `0.40`) Detection threshold

#### Response (`200 OK`):
```json
{
  "image_id": "upload_20241030_142010_123",
  "has_animal": true,
  "is_empty": false,
  "primary_species": "mountain_lion",
  "confidence": 0.942,
  "uncertainty_score": 0.12,
  "uncertainty_flags": ["High Certainty", "Low Light / IR Monochrome", "DANGEROUS: Mountain Lion / Cougar"],
  "is_rare": true,
  "is_dangerous": true,
  "alert": {
    "is_alert": true,
    "level": "CRITICAL",
    "threat_level": "Apex Carnivore (Severe Danger)",
    "rarity_status": "Vulnerable / Low Abundance",
    "headline": "CRITICAL ALERT: Mountain Lion Detected",
    "safety_advisory": "Maintain distance. Do not approach or run. Alert field rangers immediately.",
    "chime_required": true
  },
  "bounding_box": {
    "ymin": 0.28,
    "xmin": 0.22,
    "ymax": 0.76,
    "xmax": 0.68
  },
  "top_predictions": [
    { "species": "mountain_lion", "confidence": 0.942 },
    { "species": "bobcat", "confidence": 0.041 },
    { "species": "coyote", "confidence": 0.012 }
  ],
  "exif_metadata": {
    "width": 2048,
    "height": 1536,
    "is_night": true,
    "estimated_ambient_lux": 1.4
  }
}
```

---

### 3.2. `GET /api/detection/alerts`
Retrieves all historical and uploaded camera-trap records flagged as rare or dangerous fauna.

#### Request Query Parameters:
- `limit`: (Optional, default `100`) Max records to return
- `alert_level`: (Optional, e.g. `CRITICAL` or `WARNING`) Filter by severity tier

#### Response (`200 OK`):
```json
{
  "total_alerts": 66,
  "critical_count": 24,
  "warning_count": 42,
  "records": [
    {
      "image_id": "cct_img_014",
      "species": "mountain_lion",
      "confidence": 0.92,
      "location": "loc_07",
      "timestamp": "2024-06-12T02:14:00",
      "is_rare": true,
      "is_dangerous": true,
      "alert": {
        "level": "CRITICAL",
        "threat_level": "Apex Carnivore (Severe Danger)",
        "rarity_status": "Vulnerable / Low Abundance"
      }
    }
  ]
}
```

---

### 3.3. `POST /api/detection/predict-batch`
Accepts multi-image uploads (up to 50 files), runs burst sequence deduplication, and aggregates batch alert statistics.

#### Request:
- Content-Type: `multipart/form-data`
- Form Parameters:
  - `files`: Array of image files
  - `location`: (Optional) Camera station ID

#### Key Response Attributes:
- `total_uploaded`: Count of images processed
- `empty_count`: Count of false triggers filtered
- `batch_alerts_summary`:
  - `has_critical_alerts`: Boolean indicator of dangerous carnivores
  - `has_warning_alerts`: Boolean indicator of rare/vulnerable species
  - `critical_count`: Integer count
  - `warning_count`: Integer count
  - `flagged_species`: Array of unique alerted species
  - `safety_advisories`: Array of protective ranger instructions
- `results`: Array of individual image prediction objects with `is_rare`, `is_dangerous`, and `alert` blocks.

---

### 3.4. `GET /api/analytics/temporal`
Returns 24-hour circular activity profiles, diurnal vs nocturnal proportions, and hourly activity heatmaps across species.

#### Response (`200 OK`):
```json
{
  "hourly_distribution": [
    { "hour": 0, "total_sightings": 42, "species_breakdown": { "coyote": 24, "opossum": 12, "bobcat": 6 } },
    { "hour": 1, "total_sightings": 55, "species_breakdown": { "coyote": 30, "opossum": 15, "bobcat": 10 } }
  ],
  "diel_classifications": {
    "coyote": { "category": "Nocturnal / Cathemeral", "night_pct": 78.4, "day_pct": 21.6 },
    "mule_deer": { "category": "Crepuscular", "dawn_dusk_pct": 68.2, "day_pct": 22.1, "night_pct": 9.7 },
    "bird": { "category": "Strictly Diurnal", "day_pct": 96.5, "night_pct": 3.5 }
  }
}
```

---

### 3.3. `POST /api/featherless/summary`
Generates comprehensive natural-language ecological synthesis using Featherless AI (or built-in ecological engine if offline).

#### Request:
```json
{
  "date_range": { "start": "2024-06-01", "end": "2024-06-30" },
  "locations": ["loc_01", "loc_03", "loc_07"],
  "species_filter": ["coyote", "bobcat", "mule_deer"],
  "custom_prompt": "Highlight apex predator encounters and time-of-day overlap with mule deer."
}
```

#### Response (`200 OK`):
```json
{
  "provider": "Featherless AI (meta-llama/Meta-Llama-3.1-8B-Instruct)",
  "summary_markdown": "### Executive Wildlife Assessment\nAcross monitored locations **loc_01**, **loc_03**, and **loc_07** during June 2024, camera traps recorded **1,420 total exposures**...\n\n* **Empty Filtering**: 68.4% of frames were identified as empty false triggers...\n* **Predator-Prey Dynamics**: Coyote and Bobcat detections peaked between 01:00 and 04:30...",
  "generated_at": "2024-10-30T14:55:00Z",
  "tokens_used": 684
}
```

---

### 3.4. `POST /api/featherless/explain`
Generates visual and morphological explanation for a specific detection.

#### Request:
```json
{
  "image_id": "cct_img_001",
  "species": "bobcat",
  "confidence": 0.912,
  "uncertainty_flags": ["Low Light / IR Monochrome"]
}
```

#### Response (`200 OK`):
```json
{
  "explanation": "Identified as **Bobcat (Lynx rufus)** with 91.2% confidence. The subject displays distinctive morphological markers: short bobbed tail with dark dorsal bars, tufted ear tips, and facial ruffs. Although captured under monochrome infrared night-vision illumination, the cranial aspect ratio and leg-to-body proportions distinguish it clearly from domestic felids.",
  "diagnostic_alerts": ["Nocturnal IR capture — minor motion blur on hind limb"]
}
```
