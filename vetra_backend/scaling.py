from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Tuple

import cv2
import numpy as np

from . import config


def _get_aruco_dict_id(dict_name: str = "DICT_4X4_50"):
    name = dict_name.upper()
    mapping = {
        "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
        "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
        "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
        "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
        "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
        "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
        "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
        "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
        "DICT_APRILTAG_36H11": cv2.aruco.DICT_APRILTAG_36h11,
    }
    if name not in mapping:
        raise ValueError(f"Unknown ArUco dict: {dict_name}")
    return mapping[name]


def detect_aruco_markers(img_bgr: np.ndarray, dict_name: str = config.ARUCO_DICT_NAME):
    """Return (corners, ids). corners: list of (4,2) arrays."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    dict_id = _get_aruco_dict_id(dict_name)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)

    try:
        params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, params)
        corners, ids, _ = detector.detectMarkers(gray)
    except AttributeError:
        params = cv2.aruco.DetectorParameters_create()
        corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=params)

    if ids is None or len(corners) == 0:
        return [], None
    cleaned = [np.squeeze(c) for c in corners if np.squeeze(c).shape == (4, 2)]
    return cleaned, ids


def compute_cm_per_pixel_from_aruco(corners, marker_size_cm: float):
    if not corners:
        raise RuntimeError("No ArUco corners provided.")
    edges = []
    for c in corners:
        edges.extend(
            [
                np.linalg.norm(c[0] - c[1]),
                np.linalg.norm(c[1] - c[2]),
                np.linalg.norm(c[2] - c[3]),
                np.linalg.norm(c[3] - c[0]),
            ]
        )
    if not edges:
        raise RuntimeError("Failed to compute ArUco edge lengths.")
    mean_edge_px = float(np.mean(edges))
    return {
        "cm_per_pixel": marker_size_cm / mean_edge_px,
        "mean_edge_px": mean_edge_px,
        "num_markers": len(corners),
    }


@dataclass
class ScalingEngine:
    method: str
    cm_per_pixel: float
    meta: dict

    @classmethod
    def from_aruco(cls, img_bgr: np.ndarray, marker_size_cm: float, dict_name: str = config.ARUCO_DICT_NAME):
        corners, ids = detect_aruco_markers(img_bgr, dict_name=dict_name)
        if ids is None or len(corners) == 0:
            raise RuntimeError("No ArUco markers detected.")

        scale_info = compute_cm_per_pixel_from_aruco(corners, marker_size_cm)
        scale_info.update(
            {
                "dict_name": dict_name,
                "marker_size_cm": marker_size_cm,
                "marker_ids": None if ids is None else ids.flatten().tolist(),
            }
        )
        return cls(method="aruco", cm_per_pixel=scale_info["cm_per_pixel"], meta=scale_info), corners, ids


def try_aruco_scale_cm_per_px(img_bgr: np.ndarray, marker_size_cm: float | None = None) -> float | None:
    try:
        engine, _, _ = ScalingEngine.from_aruco(
            img_bgr=img_bgr,
            marker_size_cm=marker_size_cm or config.DEFAULT_MARKER_SIZE_CM,
            dict_name=config.ARUCO_DICT_NAME,
        )
        return engine.cm_per_pixel
    except Exception:
        return None


def pinhole_scale_cm_per_px(
    img_width_px: int,
    focal_length_mm: float,
    object_distance_m: float,
    sensor_width_mm: float = config.SENSOR_WIDTH_MM,
) -> float:
    D_mm = object_distance_m * 1000.0
    mm_per_px = (D_mm * sensor_width_mm) / (focal_length_mm * img_width_px)
    cm_per_px = mm_per_px / 10.0
    return cm_per_px


def get_scale_cm_per_px(
    img_bgr: np.ndarray,
    focal_length_mm: float | None = None,
    object_distance_m: float | None = None,
    marker_size_cm: float | None = None,
) -> tuple[float | None, str]:
    cm_per_px = try_aruco_scale_cm_per_px(img_bgr, marker_size_cm=marker_size_cm)
    if cm_per_px is not None:
        return cm_per_px, "aruco"

    if focal_length_mm is not None and object_distance_m is not None:
        h, w = img_bgr.shape[:2]
        cm_per_px = pinhole_scale_cm_per_px(
            img_width_px=w,
            focal_length_mm=focal_length_mm,
            object_distance_m=object_distance_m,
        )
        return cm_per_px, "pinhole"

    return None, "none"


def pixel_to_cm(value_px: float | None, cm_per_px: float | None) -> float | None:
    if value_px is None or cm_per_px is None:
        return None
    return float(value_px * cm_per_px)


def ensure_float(val: Any) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
