from __future__ import annotations

import math
from functools import lru_cache
from typing import Dict, Any

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from . import config
from .scaling import pixel_to_cm


SIDE_KP_NAMES = config.SIDE_KEYPOINT_NAMES
SIDE_NAME_TO_IDX = {n: i for i, n in enumerate(SIDE_KP_NAMES)}

# Skeleton for visualization (14-kp, same as VETRA-v3.0 train-side.ipynb)
SIDE_SKELETON_EDGES = [
    (0, 3), (0, 1), (0, 2),
    (3, 4), (4, 6), (6, 5), (5, 7),
    (7, 12), (12, 8), (8, 10),
    (8, 9),
    (9, 13), (3, 13),
    (10, 11), (8, 11),
    (10, 6),
]

# Trait connections (length-style) based on the 14-kp training notebook
SIDE_TRAIT_CONNECTIONS = {
    "stature": [("spine_mid_hips", "hoof_rear_left")],
    "heart_girth": [("spine_last_rib_top", "elbow_point")],
    "body_length": [("shoulder_point", "pin_left")],
    "body_depth": [("spine_last_rib_top", "barrel_last_rib_bottom")],
    "udder_depth": [("udder_floor_centre_rear", "hock_left"), ("udder_floor_centre_rear", "hoof_rear_left")],
}
SIDE_TRAIT_EDGES_IDX = {
    trait: [(SIDE_NAME_TO_IDX[a], SIDE_NAME_TO_IDX[b]) for (a, b) in edges]
    for trait, edges in SIDE_TRAIT_CONNECTIONS.items()
}

# Multipliers for symmetric traits
SIDE_VIEW_LENGTH_TRAITS = {
    "stature": {"multiplier": 1.0},
    "heart_girth": {"multiplier": 2.0},
    "body_length": {"multiplier": 1.0},
    "body_depth": {"multiplier": 2.0},
    "udder_depth": {"multiplier": 1.0},
}


def _safe_point(kpts: np.ndarray, idx: int):
    if idx < 0 or idx >= len(kpts):
        return None
    x, y = kpts[idx]
    if np.isnan(x) or np.isnan(y):
        return None
    return np.array([float(x), float(y)], dtype=np.float32)


def _extract_best_keypoints(res) -> np.ndarray:
    if not hasattr(res, "keypoints") or res.keypoints is None:
        raise RuntimeError("Result has no keypoints.")
    k_xy = res.keypoints.xy
    if k_xy is None or len(k_xy) == 0:
        raise RuntimeError("No keypoint detections.")
    try:
        k_conf = res.keypoints.conf
        best_idx = int(k_conf.mean(dim=1).argmax())
    except Exception:
        best_idx = 0
    return k_xy[best_idx].cpu().numpy()


@lru_cache(maxsize=1)
def load_side_model(device: str | None = None) -> YOLO:
    device = device or config.DEFAULT_DEVICE
    model = YOLO(str(config.SIDE_MODEL_PATH))
    kpt_shape = getattr(model.model, "yaml", {}).get("kpt_shape")
    if kpt_shape and kpt_shape[0] != len(SIDE_KP_NAMES):
        raise RuntimeError(
            f"Side model predicts {kpt_shape[0]} keypoints but config.SIDE_KEYPOINT_NAMES "
            f"lists {len(SIDE_KP_NAMES)}; update the names to match the checkpoint."
        )
    model.to(device)
    return model


def compute_trait_lengths_pixels(kpts_xy: np.ndarray) -> Dict[str, Dict[str, Any]]:
    measurements = {}
    for trait, edges in SIDE_TRAIT_EDGES_IDX.items():
        segment_lengths = []
        valid_segments = []
        for i, j in edges:
            p1 = _safe_point(kpts_xy, i)
            p2 = _safe_point(kpts_xy, j)
            if p1 is None or p2 is None:
                continue
            segment_lengths.append(float(math.dist(p1, p2)))
            valid_segments.append((i, j))
        if not segment_lengths:
            continue

        one_side = float(sum(segment_lengths))
        mult = SIDE_VIEW_LENGTH_TRAITS.get(trait, {}).get("multiplier", 1.0)
        measurements[trait] = {
            "total_length_px": one_side * mult,
            "total_length_px_one_side": one_side,
            "segment_lengths_px": segment_lengths,
            "segments": valid_segments,
            "multiplier": mult,
        }
    return measurements


def score_rump_angle(kpts: np.ndarray, img_height: float, tol_frac: float = 0.02):
    hook = _safe_point(kpts, SIDE_NAME_TO_IDX["hook_left"])
    pin = _safe_point(kpts, SIDE_NAME_TO_IDX["pin_left"])
    if hook is None or pin is None:
        return None
    dy = pin[1] - hook[1]
    tol = tol_frac * img_height
    if dy < -tol:
        score, label = 1, "High"
    elif dy > tol:
        score, label = 9, "Low"
    else:
        score, label = 5, "Intermediate"
    return {"score": score, "label": label, "dy_px": float(dy)}


def score_rear_legs_set(kpts: np.ndarray):
    hoof = _safe_point(kpts, SIDE_NAME_TO_IDX["hoof_rear_left"])
    pin = _safe_point(kpts, SIDE_NAME_TO_IDX["pin_left"])
    if hoof is None or pin is None:
        return None
    v = pin - hoof
    angle = abs(math.degrees(math.atan2(abs(v[0]), abs(v[1]) + 1e-6)))
    if angle <= 8.0:
        score, label = 1, "Straight"
    elif angle >= 18.0:
        score, label = 9, "Curved"
    else:
        score, label = 5, "Intermediate"
    return {"score": score, "label": label, "angle_deg": float(angle)}


def score_foot_angle(kpts: np.ndarray):
    hoof = _safe_point(kpts, SIDE_NAME_TO_IDX["hoof_rear_left"])
    toe = _safe_point(kpts, SIDE_NAME_TO_IDX["hoof_toe_tip_left"])
    heel = _safe_point(kpts, SIDE_NAME_TO_IDX["hoof_heel_hairline_left"])
    if hoof is None or toe is None or heel is None:
        return None

    v1 = hoof - toe
    v2 = heel - toe
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return None
    cosang = float(np.dot(v1, v2) / (n1 * n2))
    cosang = max(min(cosang, 1.0), -1.0)
    angle = math.degrees(math.acos(cosang))

    if angle >= 140.0:
        score, label = 1, "Low"
    elif angle <= 100.0:
        score, label = 9, "Steep"
    else:
        score, label = 5, "Intermediate"
    return {"score": score, "label": label, "angle_deg": float(angle)}


def score_angularity(kpts: np.ndarray):
    top = _safe_point(kpts, SIDE_NAME_TO_IDX["spine_last_rib_top"])
    bottom = _safe_point(kpts, SIDE_NAME_TO_IDX["barrel_last_rib_bottom"])
    if top is None or bottom is None:
        return None
    vec = bottom - top
    angle = abs(math.degrees(math.atan2(vec[0], vec[1] + 1e-6)))
    if angle <= 15.0:
        score, label = 1, "Non-angular"
    elif angle >= 35.0:
        score, label = 9, "Angular"
    else:
        score, label = 5, "Intermediate"
    return {"score": score, "label": label, "angle_deg": float(angle)}


def infer_side(img_bgr: np.ndarray, model: YOLO, device: str | None = None) -> Dict[str, Any]:
    """
    Returns:
        {
          "keypoints": np.ndarray (14,2),
          "length_traits_px": {...},
          "angle_scores": {...},
          "image_shape": (H,W)
        }
    """
    _ = device  # kept for API symmetry
    results = model(img_bgr, verbose=False)
    res = results[0]
    kpts = _extract_best_keypoints(res)
    H, W = img_bgr.shape[:2]

    length_traits_px = compute_trait_lengths_pixels(kpts)
    angle_scores = {
        "rump_angle": score_rump_angle(kpts, img_height=H),
        "rear_legs_set": score_rear_legs_set(kpts),
        "foot_angle": score_foot_angle(kpts),
        "angularity": score_angularity(kpts),
    }

    return {
        "keypoints": kpts,
        "length_traits_px": length_traits_px,
        "angle_scores": angle_scores,
        "image_shape": (H, W),
    }


def convert_length_traits_to_cm(length_px: Dict[str, Dict[str, Any]], cm_per_px: float | None):
    if cm_per_px is None:
        return None
    out = {}
    for name, info in length_px.items():
        out[name] = {
            "total_length_cm": pixel_to_cm(info["total_length_px"], cm_per_px),
            "total_length_cm_one_side": pixel_to_cm(info["total_length_px_one_side"], cm_per_px),
            "segment_lengths_cm": [pixel_to_cm(v, cm_per_px) for v in info["segment_lengths_px"]],
            "segments": info["segments"],
            "multiplier": info.get("multiplier", 1.0),
            "cm_per_px": cm_per_px,
        }
    return out
