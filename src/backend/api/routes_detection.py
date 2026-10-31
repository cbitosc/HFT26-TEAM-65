"""
Detection & Classification API Endpoints
Handles image upload, real-time animal detection, empty frame filtering,
species classification with uncertainty scores, and dataset browsing.
"""

import io
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, File, UploadFile, Form, Query, HTTPException, Response
from fastapi.responses import FileResponse
from PIL import Image

from src.backend.models.detector import detector
from src.backend.models.classifier import classifier
from src.backend.services.dataset_service import dataset_service
from src.backend.services.temporal_pooling import temporal_aggregator
from src.backend.services.excel_service import excel_service
from src.backend.services.alert_service import alert_service
from src.backend.services.duplicate_service import duplicate_service
from src.backend.config import UPLOADS_DIR, IMAGES_DIR

class BatchExcelExportRequest(BaseModel):
    items: Optional[List[Dict[str, Any]]] = None
    location: Optional[str] = "loc_01"
    timestamp: Optional[str] = None

class ClusterDuplicatesRequest(BaseModel):
    items: Optional[List[Dict[str, Any]]] = None
    similarity_threshold: Optional[float] = 0.82
    time_window_seconds: Optional[int] = 120

router = APIRouter(prefix="/api", tags=["Detection & Classification"])

@router.post("/detection/predict-image")
async def predict_single_image(
    file: UploadFile = File(...),
    location: Optional[str] = Form("loc_01"),
    datetime_str: Optional[str] = Form(None),
    threshold: Optional[float] = Form(0.45)
):
    """
    Upload an image to detect animal presence, filter empty frame,
    and classify species with confidence and uncertainty scores.
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    # Run animal detection & empty filtering
    detection_result = detector.detect(image)
    has_animal = detection_result["has_animal"]
    is_empty = detection_result["is_empty"]
    bbox = detection_result["bounding_box"]
    sensor_props = detection_result["sensor_props"]
    is_night = sensor_props.get("is_night", False)

    # Run species classification
    # At night or low light, never let detector's empty decision prematurely kill classification
    classification_result = classifier.classify_crop(
        image=image,
        bbox=bbox if has_animal else None,
        is_empty_detected=is_empty if not is_night else False,
        sensor_props=sensor_props
    )

    # Semantic Animal Verification: If the deep classifier confirms it IS an animal, ensure positive verdict
    if classification_result.get("is_animal", False):
        has_animal = True
        is_empty = False
        detection_result["has_animal"] = True
        detection_result["is_empty"] = False
        detection_result["empty_reason"] = None
        if bbox["ymax"] <= bbox["ymin"] or bbox["xmax"] <= bbox["xmin"]:
            bbox = {"ymin": 0.10, "xmin": 0.10, "ymax": 0.90, "xmax": 0.90}
    else:
        has_animal = False
        is_empty = True
        detection_result["has_animal"] = False
        detection_result["is_empty"] = True
        detected_subj = classification_result.get("detected_subject", "Non-wildlife subject")
        detection_result["empty_reason"] = f"Animal Not Detected — Non-wildlife subject detected ({detected_subj})"
        bbox = {"ymin": 0.0, "xmin": 0.0, "ymax": 0.0, "xmax": 0.0}

    # Save uploaded file
    file_id = f"upload_{uuid.uuid4().hex[:8]}"
    save_name = f"{file_id}_{file.filename}"
    save_path = UPLOADS_DIR / save_name
    image.save(save_path, "JPEG", quality=85)

    timestamp = datetime_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Evaluate Rare / Dangerous Wildlife Alert
    alert_info = classification_result.get("alert") or alert_service.evaluate_animal_alert(
        species_key=classification_result["primary_species"] if has_animal else "empty",
        common_name=classification_result["common_name"] if has_animal else "Animal Not Detected",
        confidence=classification_result["confidence"],
        location=location,
        timestamp=timestamp
    )

    rec = {
        "id": file_id,
        "file_name": save_name,
        "image_url": f"/static/uploads/{save_name}",
        "location": location,
        "datetime": timestamp,
        "seq_id": f"upload_seq_{file_id}",
        "frame_num": 0,
        "seq_num_frames": 1,
        "species": classification_result["primary_species"] if has_animal else "empty",
        "common_name": classification_result["common_name"] if has_animal else "Animal Not Detected",
        "scientific_name": "Identified Fauna" if has_animal else "Non-Wildlife / Empty",
        "is_empty": is_empty,
        "confidence": classification_result["confidence"],
        "bbox": [bbox["ymin"], bbox["xmin"], bbox["ymax"], bbox["xmax"]],
        "uncertainty_flags": classification_result["uncertainty_flags"],
        "is_night": bool(is_night or classification_result.get("night_mode_active", False)),
        "is_upload": True,
        "is_rare": alert_info.get("is_rare", False),
        "is_dangerous": alert_info.get("is_dangerous", False),
        "alert": alert_info
    }

    # Register in gallery immediately only if animal is detected!
    if has_animal:
        dataset_service.add_upload(rec)

    return {
        "image_id": file_id,
        "file_name": save_name,
        "image_url": f"/static/uploads/{save_name}",
        "location": location,
        "datetime": timestamp,
        "has_animal": has_animal,
        "is_empty": is_empty,
        "detection_confidence": detection_result["confidence"],
        "empty_reason": detection_result["empty_reason"],
        "bounding_box": bbox,
        "sensor_props": sensor_props,
        "is_rare": alert_info.get("is_rare", False),
        "is_dangerous": alert_info.get("is_dangerous", False),
        "alert": alert_info,
        **classification_result
    }

@router.post("/detection/predict-batch")
async def predict_batch_images(
    files: List[UploadFile] = File(...),
    location: Optional[str] = Form("loc_01")
):
    """
    Batch upload multiple camera-trap images for bulk inference.
    Classifies all images simultaneously and adds them to the live research gallery.
    """
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 images per batch request.")

    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for file in files:
        try:
            contents = await file.read()
            img = Image.open(io.BytesIO(contents)).convert("RGB")
            det = detector.detect(img)
            sensor_props = det["sensor_props"]
            is_night = sensor_props.get("is_night", False)

            cls = classifier.classify_crop(
                image=img,
                bbox=det["bounding_box"] if det["has_animal"] else None,
                is_empty_detected=det["is_empty"] if not is_night else False,
                sensor_props=sensor_props
            )

            # Semantic animal verification
            is_animal = bool(cls.get("is_animal", False))
            has_animal = is_animal
            is_empty = not is_animal

            if is_animal:
                bbox = det["bounding_box"]
                if bbox["ymax"] <= bbox["ymin"] or bbox["xmax"] <= bbox["xmin"]:
                    bbox = {"ymin": 0.10, "xmin": 0.10, "ymax": 0.90, "xmax": 0.90}
                empty_reason = None
            else:
                bbox = {"ymin": 0.0, "xmin": 0.0, "ymax": 0.0, "xmax": 0.0}
                detected_subj = cls.get("detected_subject", "Non-wildlife subject")
                empty_reason = f"Animal Not Detected — Non-wildlife subject detected ({detected_subj})"

            file_id = f"upload_{uuid.uuid4().hex[:8]}"
            save_name = f"{file_id}_{file.filename}"
            img.save(UPLOADS_DIR / save_name, "JPEG", quality=85)

            # Evaluate Rare / Dangerous Wildlife Alert
            alert_info = cls.get("alert") or alert_service.evaluate_animal_alert(
                species_key=cls["primary_species"] if is_animal else "empty",
                common_name=cls["common_name"] if is_animal else "Animal Not Detected",
                confidence=cls["confidence"],
                location=location,
                timestamp=timestamp
            )

            rec = {
                "id": file_id,
                "file_name": save_name,
                "image_url": f"/static/uploads/{save_name}",
                "location": location,
                "datetime": timestamp,
                "seq_id": f"upload_seq_{file_id}",
                "frame_num": 0,
                "seq_num_frames": 1,
                "species": cls["primary_species"] if is_animal else "empty",
                "common_name": cls["common_name"] if is_animal else "Animal Not Detected",
                "scientific_name": "Identified Fauna" if is_animal else "Non-Wildlife / Empty",
                "is_empty": is_empty,
                "confidence": cls["confidence"],
                "bbox": [
                    bbox["ymin"],
                    bbox["xmin"],
                    bbox["ymax"],
                    bbox["xmax"]
                ],
                "uncertainty_flags": cls["uncertainty_flags"],
                "is_night": bool(is_night or cls.get("night_mode_active", False)),
                "is_upload": True,
                "is_rare": alert_info.get("is_rare", False),
                "is_dangerous": alert_info.get("is_dangerous", False),
                "alert": alert_info
            }

            # Register upload into live gallery only if animal is detected!
            if has_animal:
                dataset_service.add_upload(rec)

            results.append({
                "image_id": file_id,
                "file_name": file.filename,
                "saved_file": save_name,
                "image_url": f"/static/uploads/{save_name}",
                "location": location,
                "datetime": timestamp,
                "timestamp": timestamp,
                "has_animal": has_animal,
                "is_empty": is_empty,
                "empty_reason": empty_reason,
                "bounding_box": bbox,
                "is_night": bool(is_night or cls.get("night_mode_active", False)),
                "is_upload": True,
                "is_rare": alert_info.get("is_rare", False),
                "is_dangerous": alert_info.get("is_dangerous", False),
                "alert": alert_info,
                **cls
            })
        except Exception as e:
            results.append({
                "file_name": file.filename,
                "error": str(e)
            })

    # Apply Temporal Context Aggregation Wrapper across consecutive burst frames (3-to-5 window)
    results = temporal_aggregator.aggregate_burst_records(results, window_size=3)

    # Synchronize any rescued records in the dataset service
    for r in results:
        if "Temporal Burst Context Rescued (Anchor Frame Pooling)" in r.get("uncertainty_flags", []):
            for u in dataset_service.uploaded_records:
                if u.get("id") == r.get("image_id"):
                    u["confidence"] = r.get("confidence", u["confidence"])
                    u["species"] = r.get("species", u["species"])
                    u["common_name"] = r.get("common_name", u["common_name"])
                    u["uncertainty_flags"] = r.get("uncertainty_flags", u["uncertainty_flags"])

    # Duplicate Image Detection & Sighting Clustering
    dedup_output = duplicate_service.group_similar_images(results)
    results = dedup_output["records"]

    # Synchronize duplicate clustering info into uploaded records
    for r in results:
        for u in dataset_service.uploaded_records:
            if u.get("id") == r.get("image_id"):
                u["cluster_id"] = r.get("cluster_id")
                u["is_anchor"] = r.get("is_anchor", True)
                u["is_representative"] = r.get("is_representative", True)
                u["is_duplicate"] = r.get("is_duplicate", False)
                u["duplicate_of"] = r.get("duplicate_of")
                u["similarity_to_anchor"] = r.get("similarity_to_anchor", 1.0)
                u["duplicate_tier"] = r.get("duplicate_tier", "UNIQUE")

    # Batch Alert Compilation
    batch_alerts_summary = alert_service.summarize_batch_alerts(results)
    empty_count = sum(1 for r in results if r.get("is_empty", False))

    duplicate_summary = {
        "total_images": dedup_output["total_images"],
        "unique_encounters_count": dedup_output["unique_encounters_count"],
        "duplicate_images_count": dedup_output["duplicate_images_count"],
        "workload_reduction_pct": dedup_output["workload_reduction_pct"],
        "multi_frame_clusters_count": dedup_output["multi_frame_clusters_count"],
        "singletons_count": dedup_output["singletons_count"],
        "clusters": dedup_output["clusters"]
    }

    return {
        "timestamp": timestamp,
        "location": location,
        "total_processed": len(results),
        "animals_detected_count": len(results) - empty_count,
        "empty_filtered_count": empty_count,
        "empty_filtered_pct": round(empty_count / len(results) * 100.0, 1) if results else 0.0,
        "has_alerts": batch_alerts_summary["has_alerts"],
        "rare_alerts_count": batch_alerts_summary["rare_alerts_count"],
        "dangerous_alerts_count": batch_alerts_summary["dangerous_alerts_count"],
        "critical_alerts_count": batch_alerts_summary["critical_alerts_count"],
        "alert_summary": batch_alerts_summary,
        "duplicate_summary": duplicate_summary,
        "items": results
    }

@router.post("/detection/cluster-duplicates")
async def cluster_duplicate_images(req: ClusterDuplicatesRequest):
    """
    Groups camera-trap records into near-duplicate and burst sighting clusters.
    Returns anchor frames, duplicate relations, and review workload reduction metrics.
    """
    items = req.items
    if not items:
        # Default to all recent uploaded records
        items = dataset_service.uploaded_records
    if not items:
        return {
            "total_images": 0,
            "unique_encounters_count": 0,
            "duplicate_images_count": 0,
            "workload_reduction_pct": 0.0,
            "clusters": []
        }
    return duplicate_service.group_similar_images(
        items,
        similarity_threshold=req.similarity_threshold,
        burst_time_window=req.time_window_seconds
    )

@router.get("/detection/duplicate-clusters")
async def get_recent_duplicate_clusters():
    """
    Fetches recent duplicate and burst sequence clusters across uploaded camera-trap images.
    """
    if not dataset_service.uploaded_records:
        return {
            "total_images": 0,
            "unique_encounters_count": 0,
            "duplicate_images_count": 0,
            "workload_reduction_pct": 0.0,
            "clusters": []
        }
    return duplicate_service.group_similar_images(dataset_service.uploaded_records)

@router.get("/detection/alerts")
async def get_recent_wildlife_alerts(limit: int = Query(20, ge=1, le=100)):
    """
    Returns recent rare animal and dangerous wildlife alerts across uploads.
    """
    alerts = []
    for u in dataset_service.uploaded_records:
        if u.get("is_rare") or u.get("is_dangerous") or (u.get("alert") and u["alert"].get("has_alert")):
            alerts.append(u.get("alert") or alert_service.evaluate_animal_alert(
                species_key=u.get("species", "empty"),
                common_name=u.get("common_name", ""),
                confidence=float(u.get("confidence", 0.0)),
                location=u.get("location", "loc_01"),
                timestamp=u.get("datetime")
            ))
    return {
        "total_alerts": len(alerts),
        "alerts": alerts[:limit]
    }

@router.post("/detection/export-batch-excel")
async def export_batch_excel_post(req: BatchExcelExportRequest):
    """
    Exports uploaded batch camera-trap detections into a formatted Excel (.xlsx) file.
    Includes summary metrics, species breakdown counts ("how many are there"), and per-image timestamps.
    """
    items = req.items
    if not items:
        # Fall back to recent uploads if items not in body
        items = dataset_service.uploaded_records
    if not items:
        raise HTTPException(status_code=400, detail="No batch records available to export.")

    export_time = req.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    excel_bytes = excel_service.generate_batch_excel_report(
        batch_data={"items": items},
        location=req.location or "loc_01",
        export_time=export_time
    )
    safe_time = export_time.replace(":", "-").replace(" ", "_")
    file_name = f"wildlife_batch_summary_{safe_time}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/detection/export-batch-excel")
async def export_batch_excel_get(location: Optional[str] = "loc_01"):
    """
    Convenience GET endpoint to download recent batch uploads as a formatted Excel (.xlsx) report.
    """
    items = dataset_service.uploaded_records
    if not items:
        raise HTTPException(status_code=404, detail="No upload records found to export.")
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    excel_bytes = excel_service.generate_batch_excel_report(
        batch_data={"items": items},
        location=location or "loc_01",
        export_time=export_time
    )
    safe_time = export_time.replace(":", "-").replace(" ", "_")
    file_name = f"wildlife_batch_summary_{safe_time}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/dataset/summary")
async def get_dataset_summary():
    """Returns Caltech Camera Traps dataset summary, locations, and category metadata."""
    ds = dataset_service.get_dataset()
    total_imgs = ds.get("total_images", 243100 + len(dataset_service.uploaded_records))
    total_anns = ds.get("total_annotations", 245118 + len(dataset_service.uploaded_records))
    return {
        "info": ds["info"],
        "total_images": total_imgs,
        "total_annotations": total_anns,
        "locations": ds["locations"],
        "categories": ds["categories"]
    }

@router.get("/dataset/images")
async def get_dataset_images(
    species: Optional[str] = Query(None, description="Comma-separated species filter"),
    locations: Optional[str] = Query(None, description="Comma-separated location IDs"),
    include_empty: bool = Query(True, description="Whether to include empty frames"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold"),
    alerts_only: bool = Query(False, description="Whether to only show rare or dangerous animal alerts"),
    deduplicate_bursts: bool = Query(False, description="Collapse duplicate burst frames into unique encounters only"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Paginated query for camera-trap images with multiple filter criteria.
    Real user uploaded images appear first!
    """
    species_list = [s.strip() for s in species.split(",")] if species else None
    locations_list = [l.strip() for l in locations.split(",")] if locations else None

    return dataset_service.query_records(
        species=species_list,
        locations=locations_list,
        include_empty=include_empty,
        min_confidence=min_confidence,
        alerts_only=alerts_only,
        deduplicate_bursts=deduplicate_bursts,
        limit=limit,
        offset=offset
    )

@router.delete("/dataset/images/{image_id}")
async def delete_gallery_image(image_id: str):
    """Deletes an image from the live research gallery and storage."""
    success = dataset_service.remove_record(image_id)
    # Also attempt direct disk removal if matches
    for p in UPLOADS_DIR.glob(f"*{image_id}*"):
        try:
            p.unlink()
            success = True
        except Exception:
            pass
    return {"success": success, "image_id": image_id}

@router.get("/dataset/image-proxy/{file_name}")
async def get_caltech_image_proxy(file_name: str):
    """
    High-speed streaming & local cache proxy for the official Caltech Camera Traps (CCT-20) 243,100 dataset.
    Streams directly from the official LILA Azure CDN and caches locally on disk for zero-latency retrieval.
    """
    # 1. Local disk cache hit
    local_path = IMAGES_DIR / file_name
    if local_path.exists():
        return FileResponse(local_path, media_type="image/jpeg")

    upload_path = UPLOADS_DIR / file_name
    if upload_path.exists():
        return FileResponse(upload_path, media_type="image/jpeg")

    # 2. Stream from official LILA Azure CDN
    cdn_url = f"https://lilawildlife.blob.core.windows.net/lila-wildlife/caltech-unzipped/cct_images/{file_name}"
    try:
        import urllib.request
        req = urllib.request.Request(cdn_url, headers={"User-Agent": "WildlifeAI/2.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read()
            # Save to disk cache
            try:
                local_path.write_bytes(content)
            except Exception:
                pass
            return Response(content=content, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})
    except Exception:
        pass

    # 3. Fallback procedural donor image
    fallback_path = dataset_service._generate_synthetic_camera_image(
        file_name=file_name,
        species="fauna",
        is_empty=False,
        is_night=False,
        location_id="cct",
        timestamp_str=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return FileResponse(fallback_path, media_type="image/jpeg")
