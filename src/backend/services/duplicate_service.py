"""
Duplicate Image Detection & Sighting Cluster Service
AI-Powered Wildlife Monitoring & Camera-Trap Analytics System
Team 65: The Chosen One | CBIT Hacktoberfest '26

Detects near-duplicate, burst sequence, and redundant camera-trap images
using perceptual hashing (dHash, aHash), structural luminance analysis,
and spatiotemporal clustering. Groups redundant frames into Sighting Clusters
to eliminate repetitive manual review work for wildlife researchers.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import os
from pathlib import Path
from datetime import datetime
from PIL import Image

class DuplicateDetectorService:
    """
    Perceptual hashing and clustering service for camera-trap burst frames.
    """

    def __init__(
        self,
        hash_size: int = 8,
        visual_similarity_threshold: float = 0.82,
        exact_duplicate_threshold: float = 0.96,
        burst_time_window_seconds: int = 120
    ):
        self.hash_size = hash_size
        self.visual_similarity_threshold = visual_similarity_threshold
        self.exact_duplicate_threshold = exact_duplicate_threshold
        self.burst_time_window_seconds = burst_time_window_seconds

    def compute_hashes_from_path_or_image(
        self,
        image_input: Union[str, Path, Image.Image, bytes]
    ) -> Dict[str, Any]:
        """
        Computes 64-bit dHash (difference hash), aHash (average hash),
        and image sharpness metrics.
        """
        img = None
        try:
            if isinstance(image_input, (str, Path)):
                img = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                img = image_input
            elif isinstance(image_input, bytes):
                import io
                img = Image.open(io.BytesIO(image_input))
            else:
                return self._empty_hash_dict()

            # Ensure image is in grayscale for perceptual hashing
            gray = img.convert('L')

            # 1. dHash (Difference Hash: detects gradient/edge direction)
            # Resize to (hash_size + 1, hash_size)
            d_img = gray.resize((self.hash_size + 1, self.hash_size), Image.Resampling.BILINEAR)
            d_pixels = list(getattr(d_img, 'get_flattened_data', d_img.getdata)())
            d_bits = []
            width = self.hash_size + 1
            for y in range(self.hash_size):
                row = d_pixels[y * width : (y + 1) * width]
                for x in range(self.hash_size):
                    d_bits.append(1 if row[x + 1] > row[x] else 0)

            # 2. aHash (Average Hash: detects overall luminosity layout)
            a_img = gray.resize((self.hash_size, self.hash_size), Image.Resampling.BILINEAR)
            a_pixels = list(getattr(a_img, 'get_flattened_data', a_img.getdata)())
            avg_lum = sum(a_pixels) / max(1, len(a_pixels))
            a_bits = [1 if p > avg_lum else 0 for p in a_pixels]

            # 3. Simple Sharpness Proxy (Variance of high-contrast adjacent pixels)
            sharpness_val = 0.0
            if len(d_pixels) > 1:
                diffs = [abs(d_pixels[i] - d_pixels[i - 1]) for i in range(1, len(d_pixels))]
                sharpness_val = sum(diffs) / max(1, len(diffs))

            # Hex string representations (64-bit -> 16 hex chars)
            d_hex = '{:016x}'.format(int(''.join(str(b) for b in d_bits), 2)) if d_bits else '0' * 16
            a_hex = '{:016x}'.format(int(''.join(str(b) for b in a_bits), 2)) if a_bits else '0' * 16

            return {
                "dhash": d_hex,
                "ahash": a_hex,
                "d_bits": d_bits,
                "a_bits": a_bits,
                "sharpness": round(sharpness_val, 2),
                "is_valid": True
            }
        except Exception:
            return self._empty_hash_dict()

    def _empty_hash_dict(self) -> Dict[str, Any]:
        zeros = [0] * (self.hash_size * self.hash_size)
        return {
            "dhash": "0" * 16,
            "ahash": "0" * 16,
            "d_bits": zeros,
            "a_bits": zeros,
            "sharpness": 0.0,
            "is_valid": False
        }

    def compute_visual_similarity(
        self,
        hash1: Dict[str, Any],
        hash2: Dict[str, Any]
    ) -> float:
        """
        Computes composite perceptual visual similarity score in range [0.0, 1.0].
        Weights dHash (70%) and aHash (30%).
        """
        if not hash1.get("is_valid") or not hash2.get("is_valid"):
            return 0.0

        b1_d = hash1.get("d_bits", [])
        b2_d = hash2.get("d_bits", [])
        b1_a = hash1.get("a_bits", [])
        b2_a = hash2.get("a_bits", [])

        if not b1_d or not b2_d or len(b1_d) != len(b2_d):
            return 0.0

        # Hamming distance for dHash
        d_diffs = sum(1 for x, y in zip(b1_d, b2_d) if x != y)
        d_sim = 1.0 - (d_diffs / len(b1_d))

        # Hamming distance for aHash
        a_diffs = sum(1 for x, y in zip(b1_a, b2_a) if x != y)
        a_sim = 1.0 - (a_diffs / len(b1_a))

        composite = (0.70 * d_sim) + (0.30 * a_sim)
        return round(max(0.0, min(1.0, composite)), 4)

    def _parse_timestamp(self, ts: Any) -> Optional[datetime]:
        """Safely parses a timestamp string or returns None."""
        if not ts:
            return None
        if isinstance(ts, datetime):
            return ts
        try:
            cleaned = str(ts).replace('T', ' ').split('.')[0]
            return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                return datetime.strptime(str(ts)[:10], "%Y-%m-%d")
            except Exception:
                return None

    def select_anchor_frame(self, members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Selects the best representative / anchor frame from a cluster of similar images.
        Criteria:
        1. Animal presence (has_animal=True is preferred over false trigger)
        2. Higher classifier confidence
        3. Higher image sharpness
        4. Lower uncertainty score
        """
        if not members:
            return {}
        if len(members) == 1:
            return members[0]

        def anchor_score(rec: Dict[str, Any]) -> float:
            score = 0.0
            # Animal presence is highest priority
            if rec.get("has_animal") and not rec.get("is_empty", False):
                score += 10.0

            # Confidence contribution
            conf = float(rec.get("confidence") or 0.0)
            score += conf * 5.0

            # Sharpness contribution
            sharpness = float(rec.get("sharpness") or 0.0)
            score += min(2.0, sharpness / 20.0)

            # Uncertainty penalty
            unc = float(rec.get("uncertainty_score") or 0.0)
            score -= min(2.0, unc)

            # Bounding box presence
            bbox = rec.get("bounding_box") or {}
            if bbox and any(bbox.values()):
                score += 1.0

            return score

        # Return member with highest score
        return max(members, key=anchor_score)

    def group_similar_images(
        self,
        records: List[Dict[str, Any]],
        similarity_threshold: Optional[float] = None,
        burst_time_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Groups similar, near-duplicate, and burst sequence camera-trap records.
        Returns detailed duplicate clusters and summary metrics.
        """
        sim_threshold = similarity_threshold or self.visual_similarity_threshold
        time_window = burst_time_window or self.burst_time_window_seconds

        n = len(records)
        if n == 0:
            return {
                "total_images": 0,
                "unique_encounters_count": 0,
                "duplicate_images_count": 0,
                "workload_reduction_pct": 0.0,
                "clusters": [],
                "singletons_count": 0,
                "records": []
            }

        # Step 1: Compute hashes for any records missing them
        enriched_records = []
        for i, r in enumerate(records):
            rec = dict(r)
            # Unique identification key
            rec_id = rec.get("image_id") or rec.get("id") or rec.get("file_name") or f"img_{i}"
            rec["_dedup_id"] = str(rec_id)

            if "hash_info" not in rec or not rec["hash_info"].get("is_valid"):
                # Try finding image source path
                img_path = rec.get("image_path") or rec.get("saved_file") or rec.get("file_name")
                if img_path and not os.path.isabs(str(img_path)):
                    # Check common directories
                    from src.backend.config import UPLOADS_DIR, IMAGES_DIR
                    cand1 = UPLOADS_DIR / str(img_path)
                    cand2 = IMAGES_DIR / str(img_path)
                    if cand1.exists():
                        img_path = cand1
                    elif cand2.exists():
                        img_path = cand2

                if img_path and os.path.exists(str(img_path)):
                    h = self.compute_hashes_from_path_or_image(img_path)
                else:
                    h = self._empty_hash_dict()
                rec["hash_info"] = h
                rec["sharpness"] = h.get("sharpness", 0.0)
            else:
                rec["sharpness"] = rec["hash_info"].get("sharpness", 0.0)

            rec["_parsed_dt"] = self._parse_timestamp(rec.get("datetime") or rec.get("timestamp"))
            enriched_records.append(rec)

        # Step 2: Cluster items using spatiotemporal proximity and visual similarity
        clusters: List[List[Dict[str, Any]]] = []
        assigned_ids = set()

        for i in range(n):
            rec_a = enriched_records[i]
            id_a = rec_a["_dedup_id"]
            if id_a in assigned_ids:
                continue

            current_cluster = [rec_a]
            assigned_ids.add(id_a)

            for j in range(i + 1, n):
                rec_b = enriched_records[j]
                id_b = rec_b["_dedup_id"]
                if id_b in assigned_ids:
                    continue

                # Compute visual similarity
                vis_sim = self.compute_visual_similarity(rec_a["hash_info"], rec_b["hash_info"])

                # Determine if images match as duplicates / burst encounter
                is_duplicate = False

                # Criterion 1: High visual similarity alone (exact or near-duplicate)
                if vis_sim >= sim_threshold:
                    is_duplicate = True

                # Criterion 2: Sequence / Burst duplicate
                # Same location + same species + time proximity + moderate similarity
                loc_a = rec_a.get("location") or "loc_01"
                loc_b = rec_b.get("location") or "loc_01"
                spec_a = rec_a.get("species") or rec_a.get("primary_species") or "unknown"
                spec_b = rec_b.get("species") or rec_b.get("primary_species") or "unknown"

                if not is_duplicate and loc_a == loc_b and spec_a == spec_b:
                    # Check time difference
                    dt_a = rec_a.get("_parsed_dt")
                    dt_b = rec_b.get("_parsed_dt")
                    if dt_a and dt_b:
                        delta_sec = abs((dt_b - dt_a).total_seconds())
                        if delta_sec <= time_window and vis_sim >= 0.65:
                            is_duplicate = True
                    else:
                        # Consecutive files with same location & species & moderate similarity
                        if abs(i - j) <= 2 and vis_sim >= 0.70:
                            is_duplicate = True

                # Criterion 3: Both empty frames at same location (windblown false trigger burst)
                empty_a = rec_a.get("is_empty", False) or not rec_a.get("has_animal", True)
                empty_b = rec_b.get("is_empty", False) or not rec_b.get("has_animal", True)
                if not is_duplicate and empty_a and empty_b and loc_a == loc_b and vis_sim >= 0.75:
                    is_duplicate = True

                if is_duplicate:
                    current_cluster.append(rec_b)
                    assigned_ids.add(id_b)

            clusters.append(current_cluster)

        # Step 3: Format Cluster Objects & Assign Member Roles
        cluster_objects = []
        updated_records = []
        duplicate_images_count = 0

        for c_idx, member_list in enumerate(clusters, 1):
            cluster_id = f"cluster_{c_idx}"
            anchor = self.select_anchor_frame(member_list)
            anchor_id = anchor["_dedup_id"]
            total_members = len(member_list)

            # Determine dominant species and common name
            dom_species = anchor.get("species") or anchor.get("primary_species") or "empty"
            dom_common = anchor.get("common_name") or dom_species.replace("_", " ").title()
            is_empty_group = anchor.get("is_empty", False) or not anchor.get("has_animal", True)

            # Workload saved
            dups_in_cluster = total_members - 1
            duplicate_images_count += dups_in_cluster
            workload_saved_pct = round((dups_in_cluster / total_members) * 100.0, 1) if total_members > 1 else 0.0

            # Human-readable cluster title
            if is_empty_group:
                cluster_title = f"Empty False Trigger Burst ({total_members} redundant frames)"
            elif total_members > 1:
                cluster_title = f"{dom_common} Sighting Group ({total_members} similar pictures)"
            else:
                cluster_title = f"{dom_common} Encounter (Single Frame)"

            # Compute pairwise similarities with anchor
            member_summaries = []
            for member in member_list:
                m_id = member["_dedup_id"]
                is_anchor = (m_id == anchor_id)
                sim_to_anchor = 1.0 if is_anchor else self.compute_visual_similarity(
                    anchor["hash_info"], member["hash_info"]
                )

                if is_anchor:
                    tier = "ANCHOR_REPRESENTATIVE"
                elif sim_to_anchor >= self.exact_duplicate_threshold:
                    tier = "EXACT_DUPLICATE"
                elif sim_to_anchor >= self.visual_similarity_threshold:
                    tier = "NEAR_DUPLICATE"
                else:
                    tier = "BURST_SEQUENCE"

                # Stamp roles onto record
                member["cluster_id"] = cluster_id
                member["is_anchor"] = is_anchor
                member["is_representative"] = is_anchor
                member["is_duplicate"] = not is_anchor
                member["duplicate_of"] = None if is_anchor else anchor_id
                member["similarity_to_anchor"] = round(sim_to_anchor, 4)
                member["similarity_pct"] = round(sim_to_anchor * 100.0, 1)
                member["duplicate_tier"] = tier

                member_summary = {
                    "image_id": m_id,
                    "file_name": member.get("file_name") or member.get("saved_file"),
                    "image_url": member.get("image_url"),
                    "is_anchor": is_anchor,
                    "confidence": member.get("confidence", 0.0),
                    "similarity_to_anchor": round(sim_to_anchor, 4),
                    "similarity_pct": round(sim_to_anchor * 100.0, 1),
                    "duplicate_tier": tier
                }
                member_summaries.append(member_summary)

                # Clean internal temp fields
                member.pop("_dedup_id", None)
                member.pop("_parsed_dt", None)
                updated_records.append(member)

            # Build cluster object
            c_obj = {
                "cluster_id": cluster_id,
                "cluster_title": cluster_title,
                "species": dom_species,
                "common_name": dom_common,
                "location": anchor.get("location") or "loc_01",
                "total_frames": total_members,
                "duplicate_count": dups_in_cluster,
                "workload_saved_pct": workload_saved_pct,
                "is_empty": is_empty_group,
                "anchor_image_id": anchor_id,
                "anchor_file_name": anchor.get("file_name") or anchor.get("saved_file"),
                "anchor_confidence": anchor.get("confidence", 0.0),
                "anchor_image_url": anchor.get("image_url"),
                "has_alert": bool(anchor.get("is_rare") or anchor.get("is_dangerous")),
                "members": member_summaries,
                "review_recommendation": (
                    f"Review 1 anchor frame instead of {total_members} repeated pictures. "
                    f"Saves {workload_saved_pct}% repetitive verification effort."
                ) if total_members > 1 else "Unique independent sighting."
            }
            cluster_objects.append(c_obj)

        total_encounters = len(cluster_objects)
        singletons_count = sum(1 for c in cluster_objects if c["total_frames"] == 1)
        multi_frame_clusters = [c for c in cluster_objects if c["total_frames"] > 1]
        overall_reduction_pct = round((duplicate_images_count / n) * 100.0, 1) if n > 0 else 0.0

        return {
            "total_images": n,
            "unique_encounters_count": total_encounters,
            "duplicate_images_count": duplicate_images_count,
            "workload_reduction_pct": overall_reduction_pct,
            "multi_frame_clusters_count": len(multi_frame_clusters),
            "singletons_count": singletons_count,
            "clusters": cluster_objects,
            "records": updated_records
        }

# Global singleton
duplicate_service = DuplicateDetectorService()
