# 🐾 Caltech Camera Traps (CCT) Dataset & Ecological Processing Guide

**Dataset Reference:** [LILA BC - Caltech Camera Traps](https://lila.science/datasets/caltech-camera-traps)  
**Format:** COCO Camera Traps (CCT) Extended JSON Specification

---

## 1. Dataset Overview

The **Caltech Camera Traps (CCT)** dataset is one of the premier open benchmarks in ecological computer vision, compiled by Caltech in collaboration with wildlife biologists. It contains approximately **243,100 camera-trap images** captured across **140 camera locations** in the Southwestern United States.

### Key Characteristics:
* **Severe Class Imbalance & Empty Frames**: Approximately **70% of all captured frames contain no animals** (empty frames). False triggers occur constantly due to wind moving shrubbery or tall grass, direct sunlight glare, sudden ambient temperature changes, and flying insects.
* **Burst Trigger Sequences**: Most camera traps fire in burst sequences (e.g., 3-10 rapid shots over 2-15 seconds) whenever the passive infrared (PIR) motion sensor is tripped.
* **Environmental Variance**: Images range from full-sun desert glare to pitch-black nighttime infrared (IR) flash exposures with high ISO sensor noise, severe motion blur from running animals, and extreme eye shine (*tapetum lucidum* reflection).

---

## 2. COCO Camera Traps (CCT) JSON Schema

The standard CCT schema extends standard COCO object detection format with wildlife-specific telemetry attributes:

```json
{
  "info": {
    "year": 2024,
    "version": "1.0",
    "description": "Caltech Camera Traps - Wildlife Monitoring Benchmark",
    "contributor": "Caltech / LILA BC"
  },
  "categories": [
    { "id": 0, "name": "empty" },
    { "id": 1, "name": "coyote" },
    { "id": 2, "name": "bobcat" },
    { "id": 3, "name": "mule_deer" },
    { "id": 4, "name": "opossum" },
    { "id": 5, "name": "raccoon" },
    { "id": 6, "name": "mountain_lion" },
    { "id": 7, "name": "gray_fox" },
    { "id": 8, "name": "striped_skunk" },
    { "id": 9, "name": "cottontail_rabbit" },
    { "id": 10, "name": "bird" },
    { "id": 11, "name": "rodent" },
    { "id": 12, "name": "domestic_dog" }
  ],
  "images": [
    {
      "id": "cct_img_001",
      "file_name": "loc03_20240614_221530_frame0.jpg",
      "width": 2048,
      "height": 1536,
      "location": "loc_03",
      "datetime": "2024-06-14 22:15:30",
      "seq_id": "seq_loc03_20240614_01",
      "seq_num_frames": 3,
      "frame_num": 0
    }
  ],
  "annotations": [
    {
      "id": "ann_001",
      "image_id": "cct_img_001",
      "category_id": 1,
      "bbox": [512, 384, 600, 450],
      "confidence": 0.94
    }
  ]
}
```

---

## 3. The 3 Core Ecological Data Challenges & Solutions

### 3.1. Empty Frame Filtering
* **The Problem**: Field biologists spend weeks manually clicking through tens of thousands of frames that depict empty vegetation.
* **The Solution**: Our system incorporates an **automated empty detector** that scores foreground object saliency, contour energy, edge density, and spatial coherence. Frames with animal confidence $< 0.45$ (or salient area $< 0.008$) are labeled as `empty` and can be automatically hidden or purged from review queues.

### 3.2. Burst Sequence Deduplication (Independent Sighting Events)
* **The Problem**: A single wandering coyote might trigger 30 photos within two minutes. If each frame is counted as an observation, coyote abundance is overestimated by $30\times$.
* **The Solution**: The dataset service aggregates frames into **Independent Sighting Events (ISE)**:
  $$\text{Frames grouped if } \text{location}_A == \text{location}_B \quad \text{and} \quad |t_A - t_B| \le \tau \quad (\tau = 60\text{ seconds})$$
  The system computes both **Total Raw Frames** and **Independent Events** to provide biologically unbiased relative abundance indices (RAI).

### 3.3. Prediction Calibration & Uncertainty Quantification
* **The Problem**: False positives between closely related species (e.g., Coyote vs. Domestic Dog, or Gray Fox vs. Kit Fox) mislead conservation policies.
* **The Solution**: The system outputs:
  - Prediction confidence score ($0.0 - 1.0$).
  - Top-3 candidate species probabilities.
  - Uncertainty entropy: $H(p) = -\sum_{k} p_k \ln p_k$.
  - Environmental / sensor diagnostics: `Low Light / IR Monochrome`, `Motion Blur`, `Occluded Edge`, `High Certainty`.
  - Predictions with confidence $< 0.65$ or entropy $> 1.20$ are explicitly tagged with `Review Recommended`.

---

## 4. Supported Species Taxonomy

| Species Key | Common Name | Scientific Name | Trophic Level | Diel Tendency |
| :--- | :--- | :--- | :--- | :--- |
| `coyote` | Coyote | *Canis latrans* | Mesopredator / Generalist | Nocturnal / Cathemeral |
| `bobcat` | Bobcat | *Lynx rufus* | Carnivore | Crepuscular / Nocturnal |
| `mule_deer` | Mule Deer | *Odocoileus hemionus* | Herbivore | Crepuscular |
| `opossum` | Virginia Opossum | *Didelphis virginiana* | Omnivore | Strictly Nocturnal |
| `raccoon` | Raccoon | *Procyon lotor* | Omnivore | Nocturnal |
| `mountain_lion` | Mountain Lion / Cougar | *Puma concolor* | Apex Predator | Nocturnal / Crepuscular |
| `gray_fox` | Gray Fox | *Urocyon cinereoargenteus* | Mesopredator | Nocturnal / Crepuscular |
| `striped_skunk` | Striped Skunk | *Mephitis mephitis* | Omnivore | Strictly Nocturnal |
| `cottontail_rabbit` | Desert / Mountain Cottontail | *Sylvilagus audubonii* | Small Herbivore | Crepuscular / Diurnal |
| `bird` | Regional Avian Fauna | *Aves spp.* | Diverse | Strictly Diurnal |
| `rodent` | Desert Woodrat / Ground Squirrel | *Rodentia spp.* | Diverse | Diurnal / Nocturnal |
| `domestic_dog` | Domestic Dog | *Canis lupus familiaris* | Domestic / Anthropogenic | Diurnal / Anthropogenic |
| `empty` | Background / False Trigger | *N/A* | None | All hours |
