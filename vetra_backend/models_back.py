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


BACK_KP_NAMES = config.BACK_KEYPOINT_NAMES
BACK_NAME_TO_IDX = {n: i for i, n in enumerate(BACK_KP_NAMES)}

BACK_SKELETON_EDGES = [
    (BACK_NAME_TO_IDX["hoof_rear_left"], BACK_NAME_TO_IDX["hock_left"]),
    (BACK_NAME_TO_IDX["hock_left"], BACK_NAME_TO_IDX["pin_left"]),
    (BACK_NAME_TO_IDX["pin_left"], BACK_NAME_TO_IDX["hook_left"]),
    (BACK_NAME_TO_IDX["hook_left"], BACK_NAME_TO_IDX["tail_head"]),
    (BACK_NAME_TO_IDX["hoof_rear_right"], BACK_NAME_TO_IDX["hock_right"]),
    (BACK_NAME_TO_IDX["hock_right"], BACK_NAME_TO_IDX["pin_right"]),
    (BACK_NAME_TO_IDX["pin_right"], BACK_NAME_TO_IDX["hook_right"]),
    (BACK_NAME_TO_IDX["hook_right"], BACK_NAME_TO_IDX["tail_head"]),
    (BACK_NAME_TO_IDX["pin_left"], BACK_NAME_TO_IDX["pin_right"]),
    (BACK_NAME_TO_IDX["hook_left"], BACK_NAME_TO_IDX["hook_right"]),
    (BACK_NAME_TO_IDX["tail_head"], BACK_NAME_TO_IDX["vulva_bottom"]),
]

# Length traits
BACK_LENGTH_TRAITS = {
    "rump_width": [(BACK_NAME_TO_IDX["pin_left"], BACK_NAME_TO_IDX["pin_right"])],
    "hook_width": [(BACK_NAME_TO_IDX["hook_left"], BACK_NAME_TO_IDX["hook_right"])],
    "rear_udder_height": [(BACK_NAME_TO_IDX["tail_head"], BACK_NAME_TO_IDX["vulva_bottom"])],
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
def load_back_model(device: str | None = None) -> YOLO:
    device = device or config.DEFAULT_DEVICE
    model = YOLO(str(config.BACK_MODEL_PATH))
    model.to(device)
    return model


def compute_back_lengths(kpts: np.ndarray) -> Dict[str, Dict[str, Any]]:
    out = {}
    for name, edges in BACK_LENGTH_TRAITS.items():
        segs = []
        for i, j in edges:
            p1, p2 = _safe_point(kpts, i), _safe_point(kpts, j)
            if p1 is None or p2 is None:
                continue
            segs.append(float(math.dist(p1, p2)))
        if not segs:
            continue
        total = float(sum(segs))
        out[name] = {
            "total_length_px": total,
            "segment_lengths_px": segs,
            "segments": edges,
        }
    return out


def score_rump_angle_back(kpts: np.ndarray):
    hook_l = _safe_point(kpts, BACK_NAME_TO_IDX["hook_left"])
    pin_l = _safe_point(kpts, BACK_NAME_TO_IDX["pin_left"])
    hook_r = _safe_point(kpts, BACK_NAME_TO_IDX["hook_right"])
    pin_r = _safe_point(kpts, BACK_NAME_TO_IDX["pin_right"])
    diffs = []
    for hook, pin in [(hook_l, pin_l), (hook_r, pin_r)]:
        if hook is None or pin is None:
            continue
        diffs.append(pin[1] - hook[1])
    if not diffs:
        return None
    dy = float(np.mean(diffs))
    if dy < -5:
        score, label = 1, "High"
    elif dy > 5:
        score, label = 9, "Low"
    else:
        score, label = 5, "Intermediate"
    return {"score": score, "label": label, "dy_px": dy}


def score_rear_legs_rear_view(kpts: np.ndarray):
    legs = [
        (BACK_NAME_TO_IDX["hock_left"], BACK_NAME_TO_IDX["hoof_rear_left"]),
        (BACK_NAME_TO_IDX["hock_right"], BACK_NAME_TO_IDX["hoof_rear_right"]),
    ]
    angles = []
    for hock_idx, hoof_idx in legs:
        hock = _safe_point(kpts, hock_idx)
        hoof = _safe_point(kpts, hoof_idx)
        if hock is None or hoof is None:
            continue
        v = hoof - hock
        angle = abs(math.degrees(math.atan2(v[0], v[1] + 1e-6)))
        angles.append(angle)
    if not angles:
        return None
    avg_angle = float(np.mean(angles))
    if avg_angle <= 5:
        score, label = 5, "Straight"
    elif avg_angle >= 20:
        score, label = 9, "Wide set"
    else:
        score, label = 7, "Slightly wide"
    return {"score": score, "label": label, "angle_deg": avg_angle}


def score_body_condition_back(kpts: np.ndarray):
    tail = _safe_point(kpts, BACK_NAME_TO_IDX["tail_head"])
    hooks = [_safe_point(kpts, BACK_NAME_TO_IDX["hook_left"]), _safe_point(kpts, BACK_NAME_TO_IDX["hook_right"])]
    pins = [_safe_point(kpts, BACK_NAME_TO_IDX["pin_left"]), _safe_point(kpts, BACK_NAME_TO_IDX["pin_right"])]
    if tail is None or any(p is None for p in hooks + pins):
        return None
    dists = [float(math.dist(tail, p)) for p in hooks + pins]
    avg = float(np.mean(dists))
    # Higher distance -> likely more angular (lean) -> lower BCS
    if avg >= 160:
        score, label = 3, "Lean"
    elif avg <= 80:
        score, label = 8, "Well covered"
    else:
        score, label = 6, "Moderate"
    return {"score": score, "label": label, "avg_dist_px": avg}


def infer_back(img_bgr: np.ndarray, model: YOLO, device: str | None = None) -> Dict[str, Any]:
    _ = device
    results = model(img_bgr, verbose=False)
    res = results[0]
    kpts = _extract_best_keypoints(res)

    length_traits_px = compute_back_lengths(kpts)
    angle_scores = {
        "rump_angle": score_rump_angle_back(kpts),
        "rear_legs_rear_view": score_rear_legs_rear_view(kpts),
        "body_condition_score": score_body_condition_back(kpts),
    }
    return {
        "keypoints": kpts,
        "length_traits_px": length_traits_px,
        "angle_scores": angle_scores,
        "image_shape": img_bgr.shape[:2],
    }


def convert_length_traits_to_cm(length_px: Dict[str, Dict[str, Any]], cm_per_px: float | None):
    if cm_per_px is None:
        return None
    out = {}
    for name, info in length_px.items():
        out[name] = {
            "total_length_cm": pixel_to_cm(info["total_length_px"], cm_per_px),
            "segment_lengths_cm": [pixel_to_cm(v, cm_per_px) for v in info["segment_lengths_px"]],
            "segments": info["segments"],
            "cm_per_px": cm_per_px,
        }
    return out
