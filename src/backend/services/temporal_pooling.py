"""
Temporal Context Aggregation & Confidence Pooling Service
Processes consecutive camera-trap burst frames (3-to-5 frame window).
Applies rolling maximum pooling and confidence overrides so a single sharp frame
rescues adjacent dark, blurry, or low-confidence night frames.
"""

from typing import List, Dict, Any, Optional
import numpy as np

class TemporalBurstAggregator:
    """
    Aggregates classification probabilities and confidence scores across consecutive
    camera-trap burst frames.
    """

    def __init__(self, default_window_size: int = 3, temporal_decay: float = 0.95):
        self.default_window_size = default_window_size
        self.temporal_decay = temporal_decay

    def aggregate_confidence_matrices(
        self,
        confidence_matrix: np.ndarray,
        window_size: Optional[int] = None,
        decay: Optional[float] = None
    ) -> np.ndarray:
        """
        Applies temporal rolling maximum pooling over a 2D confidence matrix (T x C)
        where T is number of burst frames and C is number of classes.
        """
        w = window_size or self.default_window_size
        d = decay or self.temporal_decay
        t_steps, c_classes = confidence_matrix.shape
        if t_steps <= 1:
            return confidence_matrix.copy()

        pooled = np.zeros_like(confidence_matrix)
        half_w = w // 2

        for t in range(t_steps):
            t_start = max(0, t - half_w)
            t_end = min(t_steps, t + half_w + 1)
            
            # Compute decayed weights for each frame in the window
            candidates = []
            for k in range(t_start, t_end):
                dist = abs(t - k)
                weight = d ** dist
                candidates.append(confidence_matrix[k] * weight)
            
            # Rolling maximum pooling
            pooled[t] = np.max(np.stack(candidates, axis=0), axis=0)

        # Normalize across classes
        row_sums = np.sum(pooled, axis=1, keepdims=True)
        row_sums = np.where(row_sums > 1e-12, row_sums, 1.0)
        return pooled / row_sums

    def aggregate_burst_records(
        self,
        records: List[Dict[str, Any]],
        window_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Applies rolling maximum pooling over consecutive burst image records.
        Rescues low-confidence or blurry frames using adjacent sharp anchor frames.
        """
        w = window_size or self.default_window_size
        n = len(records)
        if n <= 1:
            return records

        pooled = [dict(r) for r in records]
        half_w = w // 2

        for i in range(n):
            curr = records[i]
            # Ignore records with errors or explicit empty frames
            if curr.get("error") or curr.get("is_empty", False):
                continue

            curr_conf = float(curr.get("confidence", 0.0))
            curr_species = curr.get("species") or curr.get("primary_species")

            start = max(0, i - half_w)
            end = min(n, i + half_w + 1)
            window = records[start:end]

            best_neighbor = None
            best_eff_conf = curr_conf

            for j_offset, neighbor in enumerate(window):
                j = start + j_offset
                if neighbor.get("error") or neighbor.get("is_empty", False):
                    continue
                dist = abs(i - j)
                neighbor_conf = float(neighbor.get("confidence", 0.0))
                eff_conf = neighbor_conf * (self.temporal_decay ** dist)

                # An anchor frame is considered valid if it has confidence >= 0.65
                if eff_conf > best_eff_conf and neighbor_conf >= 0.65:
                    best_eff_conf = eff_conf
                    best_neighbor = neighbor

            # If an adjacent anchor frame significantly outperforms this frame, pool confidence
            if best_neighbor and best_eff_conf > (curr_conf + 0.08):
                anchor_species = best_neighbor.get("species") or best_neighbor.get("primary_species")
                anchor_common = best_neighbor.get("common_name", "")
                
                pooled[i]["confidence"] = round(float(best_eff_conf), 4)
                if anchor_species:
                    pooled[i]["species"] = anchor_species
                    pooled[i]["primary_species"] = anchor_species
                if anchor_common:
                    pooled[i]["common_name"] = anchor_common
                
                flags = list(pooled[i].get("uncertainty_flags", []))
                if "Temporal Burst Context Rescued (Anchor Frame Pooling)" not in flags:
                    flags.append("Temporal Burst Context Rescued (Anchor Frame Pooling)")
                if "Review Recommended" in flags and best_eff_conf >= 0.65:
                    flags.remove("Review Recommended")
                if "High Certainty" not in flags and best_eff_conf >= 0.70:
                    flags.append("High Certainty")
                pooled[i]["uncertainty_flags"] = flags

        return pooled

# Global singleton
temporal_aggregator = TemporalBurstAggregator()
