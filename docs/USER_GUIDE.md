# 📖 Wildlife Researcher Dashboard User Guide

**Project:** AI-Powered Wildlife Monitoring & Camera-Trap Analytics System  
**Hackathon:** CBIT Hacktoberfest '26 — Team 65 (`The Chosen One`)

---

## 1. Getting Started

### 1.1. Quick Launch (One-Command Start)
All project code, virtual environment, dependencies, and datasets are hosted locally on the **D: drive**.

To start the system:
```powershell
cd D:\HFT26-TEAM-65-main
& D:\HFT26-TEAM-65-main\.venv\Scripts\python.exe -m src.backend.main
```
Or with uvicorn:
```powershell
& D:\HFT26-TEAM-65-main\.venv\Scripts\uvicorn.exe src.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open your browser at:
- **Interactive Dashboard:** `http://127.0.0.1:8000`
- **Swagger REST API Documentation:** `http://127.0.0.1:8000/docs`

---

## 2. Dashboard Feature Tour

### 2.1. Top KPI Summary Cards
- **Total Images Ingested**: Total raw frames processed from camera traps.
- **Empty Frames Filtered**: Percentage and count of empty frames eliminated (saving manual review hours).
- **Species Richness ($S$)**: Number of distinct wildlife species detected.
- **Shannon Diversity Index ($H'$)**: Biodiversity metric measuring species richness and abundance evenness.
- **Review Required**: Count of frames with low confidence ($<65\%$) or high uncertainty flags.

### 2.2. Interactive Filter Matrix
- **Species Selector**: Filter by any combination of Caltech species (Coyote, Bobcat, Mule Deer, Opossum, etc.).
- **Camera Station Selector**: Filter by deployment location (`loc_01`, `loc_02`, ..., `loc_08`).
- **Show / Hide Empty Images**: Toggle empty false triggers on/off to experience the review workload reduction.
- **Confidence Slider**: Adjust detection threshold dynamically ($0\% - 100\%$).
- **Time of Day Filter**: All hours, Day (06:00-18:00), Night (18:00-06:00), or Crepuscular (dawn/dusk).

### 2.3. Temporal & Diel Activity Visualizations
- **24-Hour Circular / Hourly Activity Curve**: Displays when species are active throughout the day and night.
- **Diel Classification Badges**: Automatically categorizes species as *Nocturnal*, *Diurnal*, or *Crepuscular*.
- **Temporal Sighting Frequency Timeline**: Tracks seasonal or daily surges in animal sightings.

### 2.4. Spatial Camera Trap Network
- **Station Activity Map**: Visual distribution of camera trap coordinates, capture density, and species co-occurrence.
- **Station Heatmap & Richness Chart**: Compares biodiversity and encounter rates across monitored habitats.

### 2.5. Representative Gallery & Bounding Box Inspector
- Displays thumbnail gallery with colored species badges, confidence bars, and uncertainty indicators.
- **Inspect Mode**: Clicking any image opens the High-Resolution Inspector displaying:
  - Green/Red/Yellow bounding box overlay around detected animal.
  - Top-3 species prediction probabilities.
  - Image metadata (Camera Station, Timestamp, Frame Number, Burst Sequence ID).
  - Environmental diagnostics (Nighttime IR mode, motion blur, occlusion).
  - **"Explain with Featherless AI"** button to generate an instant morphological rationale.

### 2.6. Drag-and-Drop Live Image Upload & Batch Inference
- Upload single or multiple camera-trap images directly from your computer.
- The AI pipeline automatically:
  1. Detects whether an animal is present or if the image is empty.
  2. Classifies species with prediction confidence.
  3. Overlays bounding boxes and uncertainty tags.
  4. Appends results to the live analytics session.

### 2.7. Featherless AI Ecological Insights Studio
- Click **"Generate Natural-Language Synthesis"** to produce a scientific executive summary of current filtered sightings.
- Custom prompt field allows researchers to ask targeted questions (e.g., "Analyze coyote and mule deer predator-prey timing").
- Copy report to clipboard or export as Markdown / PDF-ready report.

---

## 3. Running Test Suites

To execute the automated verification test suite:
```powershell
cd D:\HFT26-TEAM-65-main
& D:\HFT26-TEAM-65-main\.venv\Scripts\pytest.exe -v tests/
```
All tests verify detection, species classification, uncertainty calculation, CCT dataset parsing, temporal analytics, and Featherless AI synthesis.
