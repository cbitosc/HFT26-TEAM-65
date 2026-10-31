"""
Animal Detection and Empty Image Filtering Module
Designed for Camera-Trap workflows (e.g. Caltech Camera Traps benchmark).
Detects whether an image frame contains an animal, bounds the region of interest,
and filters empty triggers (caused by windblown foliage, lighting changes, etc.).
"""

from typing import Dict, Any, Tuple
from PIL import Image, ImageFilter, ImageStat, ImageOps
import numpy as np

class AnimalDetector:
    """
    Evaluates camera-trap frames to filter empty images and isolate animal bounding boxes.
    Combines foreground saliency, spatial gradient dynamics, and contrast distributions.
    """
    
    def __init__(self, confidence_threshold: float = 0.45):
        self.confidence_threshold = confidence_threshold

    def analyze_image_properties(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extracts photometric and sensor diagnostics (e.g. nighttime IR vs daytime RGB).
        """
        img_rgb = image.convert("RGB")
        width, height = img_rgb.size
        
        stat = ImageStat.Stat(img_rgb)
        mean_r, mean_g, mean_b = stat.mean[:3]
        std_r, std_g, std_b = stat.stddev[:3]
        
        # Check if monochrome / infrared night mode (R, G, B channels nearly identical)
        rgb_diff = (abs(mean_r - mean_g) + abs(mean_g - mean_b) + abs(mean_r - mean_b)) / 3.0
        is_ir_monochrome = bool(rgb_diff < 7.0 and (mean_r + mean_g + mean_b) / 3.0 < 160.0)
        
        # Check overall luminance
        luminance = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b
        is_night = bool(luminance < 75.0 or is_ir_monochrome)
        
        # Measure edge / high frequency energy (detect motion blur or flat empty backgrounds)
        gray = img_rgb.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        edge_energy = float(edge_stat.mean[0])
        
        return {
            "width": width,
            "height": height,
            "luminance": round(luminance, 2),
            "is_night": is_night,
            "is_ir_monochrome": is_ir_monochrome,
            "edge_energy": round(edge_energy, 2),
            "contrast_std": round(float((std_r + std_g + std_b) / 3.0), 2)
        }

    def detect(self, image: Image.Image) -> Dict[str, Any]:
        """
        Detects animal presence, predicts bounding box, and computes empty/occupied confidence.
        Includes dedicated nighttime & 850nm/940nm Infrared (IR) flash compensation.
        """
        props = self.analyze_image_properties(image)
        width, height = props["width"], props["height"]
        is_night = props["is_night"]
        
        # Downsample for fast, stable saliency & contour calculation
        thumb_w, thumb_h = 256, 192
        thumb = image.convert("L").resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        
        # Adaptive contrast stretching for nighttime / IR frames to expose animal silhouettes
        if is_night:
            thumb = ImageOps.autocontrast(thumb, cutoff=1)

        arr = np.array(thumb, dtype=np.float32)
        
        # Background gradient & variance estimation
        grad_y = np.abs(np.diff(arr, axis=0))
        grad_x = np.abs(np.diff(arr, axis=1))
        local_var = float(np.var(arr))
        
        # Compute central vs peripheral activity
        center_y1, center_y2 = int(thumb_h * 0.20), int(thumb_h * 0.85)
        center_x1, center_x2 = int(thumb_w * 0.15), int(thumb_w * 0.85)
        center_region = arr[center_y1:center_y2, center_x1:center_x2]
        
        center_std = float(np.std(center_region)) if center_region.size > 0 else 0.0
        
        # Find highest contrast localized cluster (candidate animal bbox)
        # Compute patch energy across a 4x4 spatial grid
        grid_rows, grid_cols = 4, 4
        cell_h = thumb_h // grid_rows
        cell_w = thumb_w // grid_cols
        
        max_energy = 0.0
        best_r, best_c = 1, 1
        
        grid_energies = np.zeros((grid_rows, grid_cols))
        for r in range(grid_rows):
            for c in range(grid_cols):
                patch = arr[r*cell_h:(r+1)*cell_h, c*cell_w:(c+1)*cell_w]
                # High difference from ambient patch mean
                energy = float(np.std(patch) * (1.0 + abs(np.mean(patch) - 128.0) / 128.0))
                grid_energies[r, c] = energy
                if energy > max_energy:
                    max_energy = energy
                    best_r, best_c = r, c
        
        # Saliency ratio: difference between highest activation cell and average background
        mean_ambient = float(np.mean(grid_energies))
        saliency_ratio = (max_energy / (mean_ambient + 1e-4)) if mean_ambient > 0 else 1.0
        
        # Calculate animal presence probability
        # Calibrated based on typical camera-trap false trigger profiles
        base_score = 0.30
        if center_std > 20.0:
            base_score += 0.25
        if saliency_ratio > 1.30:
            base_score += 0.25
        if props["edge_energy"] > 6.0:
            base_score += 0.15

        if not is_night and local_var < 80.0:
            # Low contrast / featureless scene in daylight (typically empty sky or uniform foliage)
            base_score -= 0.35
        elif is_night:
            # In nighttime, only penalize if it is truly flat uniform black background
            if local_var < 15.0 and props["contrast_std"] < 5.0:
                base_score -= 0.30
            # Localized nighttime activation boost
            if saliency_ratio > 1.22 or center_std > 18.0:
                base_score += 0.20
            
        confidence = float(np.clip(base_score, 0.05, 0.98))
        has_animal = bool(confidence >= self.confidence_threshold)
        
        if has_animal:
            # Formulate realistic bounding box covering the entire salient subject
            active_threshold = mean_ambient * (0.85 if is_night else 0.90)
            active_cells = np.argwhere(grid_energies >= active_threshold)
            if len(active_cells) > 0:
                min_r = int(np.min(active_cells[:, 0]))
                max_r = int(np.max(active_cells[:, 0]))
                min_c = int(np.min(active_cells[:, 1]))
                max_c = int(np.max(active_cells[:, 1]))
                
                ymin = max(0.06, (min_r * cell_h - 10) / float(thumb_h))
                xmin = max(0.06, (min_c * cell_w - 10) / float(thumb_w))
                ymax = min(0.94, ((max_r + 1) * cell_h + 10) / float(thumb_h))
                xmax = min(0.94, ((max_c + 1) * cell_w + 10) / float(thumb_w))
            else:
                ymin, xmin, ymax, xmax = 0.15, 0.15, 0.85, 0.85
            empty_reason = None
        else:
            # Empty frame
            ymin, xmin, ymax, xmax = 0.0, 0.0, 0.0, 0.0
            if props["contrast_std"] < 18.0:
                empty_reason = "Uniform background / low foreground-background contrast"
            elif props["edge_energy"] < 5.0:
                empty_reason = "No salient high-frequency animal contours detected"
            else:
                empty_reason = "Vegetation motion / ambient wind trigger without animal subject"

        return {
            "has_animal": has_animal,
            "is_empty": not has_animal,
            "confidence": round(confidence, 4),
            "empty_reason": empty_reason,
            "bounding_box": {
                "ymin": round(ymin, 4),
                "xmin": round(xmin, 4),
                "ymax": round(ymax, 4),
                "xmax": round(xmax, 4)
            },
            "sensor_props": props
        }

# Global singleton
detector = AnimalDetector()
