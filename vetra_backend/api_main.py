from __future__ import annotations

import base64
import io
from typing import Dict, Any

import cv2
import numpy as np
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .models_side import (
    load_side_model,
    infer_side,
    convert_length_traits_to_cm,
    SIDE_SKELETON_EDGES,
    SIDE_KP_NAMES,
)
from .models_back import (
    load_back_model,
    infer_back,
    convert_length_traits_to_cm as convert_back_cm,
    BACK_SKELETON_EDGES,
    BACK_KP_NAMES,
)
from .models_udder import (
    load_udder_models,
    infer_udder_side,
    infer_udder_bottom,
    UDDER_SKELETON_EDGES,
    UDDER_BOTTOM_NAMES,
)
from .scaling import get_scale_cm_per_px
from .traits import compute_all_traits
from .reporting import render_html_report

app = FastAPI(title="VETRA Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SIDE_MODEL = None
_BACK_MODEL = None
_UDDER_MODELS = None


def ensure_models():
    global _SIDE_MODEL, _BACK_MODEL, _UDDER_MODELS
    if _SIDE_MODEL is None:
        _SIDE_MODEL = load_side_model()
    if _BACK_MODEL is None:
        _BACK_MODEL = load_back_model()
    if _UDDER_MODELS is None:
        _UDDER_MODELS = load_udder_models()


async def _read_image(upload: UploadFile) -> np.ndarray:
    data = await upload.read()
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail=f"Could not decode image {upload.filename}")
    return img


def _draw_overlay(
    img_bgr: np.ndarray,
    kpts: np.ndarray,
    edges,
    names,
    traits_px: Dict[str, Any] | None = None,
    cm_per_px: float | None = None,
) -> str:
    """Matplotlib overlay similar to notebook visuals."""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.imshow(img_rgb)
    ax.axis("off")

    # skeleton
    colors = plt.cm.tab20(np.linspace(0, 1, len(edges) + 1))
    for idx, (i, j) in enumerate(edges):
        if i >= len(kpts) or j >= len(kpts):
            continue
        x1, y1 = kpts[i]
        x2, y2 = kpts[j]
        if np.isnan([x1, y1, x2, y2]).any():
            continue
        ax.plot([x1, x2], [y1, y2], color=colors[idx], linewidth=2)

    # trait lines (thicker)
    if traits_px:
        for name, info in traits_px.items():
            for (i, j), seg_len in zip(info.get("segments", []), info.get("segment_lengths_px", [])):
                if i >= len(kpts) or j >= len(kpts):
                    continue
                p1 = kpts[i]
                p2 = kpts[j]
                if np.isnan(p1).any() or np.isnan(p2).any():
                    continue
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="orange", linewidth=3)
                mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                label = f"{name}: {seg_len * cm_per_px:.1f} cm" if cm_per_px else f"{name}: {seg_len:.1f} px"
                ax.text(mid[0], mid[1], label, color="white", fontsize=8,
                        bbox=dict(facecolor="orange", alpha=0.8, edgecolor="none"))

    # keypoints + labels
    for idx, (x, y) in enumerate(kpts):
        if np.isnan([x, y]).any():
            continue
        ax.scatter(x, y, s=30, color="cyan", edgecolor="black", linewidth=0.5)
        label = names[idx] if idx < len(names) else str(idx)
        ax.text(x + 3, y - 3, f"{idx}:{label}", fontsize=7,
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"))

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def refine_scale(cm_per_px: float | None, trait_px: float | None, trait_key: str) -> float | None:
    if cm_per_px is None or trait_px is None or trait_px <= 0:
        # If no scale yet but we have a reliable trait in pixels, derive one from mid-range
        anchor_ranges = {
            "body_length": (160.0, 200.0),
            "heart_girth": (160.0, 220.0),
            "stature": (120.0, 160.0),
            "rump_width": (12.0, 20.0),
            "teat_length": (4.0, 6.5),
        }
        if trait_key in anchor_ranges:
            lo, hi = anchor_ranges[trait_key]
            mid = (lo + hi) / 2.0
            return mid / trait_px
        return cm_per_px

    anchor_ranges = {
        "body_length": (160.0, 200.0),
        "heart_girth": (160.0, 220.0),
        "stature": (120.0, 160.0),
        "rump_width": (12.0, 20.0),
        "teat_length": (4.0, 6.5),
    }
    if trait_key not in anchor_ranges:
        return cm_per_px
    lo, hi = anchor_ranges[trait_key]
    cm_val = trait_px * cm_per_px
    if lo * 0.5 <= cm_val <= hi * 1.5:
        return cm_per_px
    mid = (lo + hi) / 2.0
    return mid / trait_px


@app.post("/api/v1/analyze")
async def analyze_cow(
    side_image: UploadFile = File(...),
    back_image: UploadFile = File(...),
    udder_bottom_image: UploadFile = File(...),
    village_name: str | None = Form(None),
    farmer_name: str | None = Form(None),
    animal_tag: str | None = Form(None),
    lactation_no: str | None = Form(None),
    date_of_calving: str | None = Form(None),
    focal_length_mm: float | None = Form(None),
    object_distance_m: float | None = Form(None),
    marker_size_cm: float | None = Form(None),
):
    ensure_models()

    side_img = await _read_image(side_image)
    back_img = await _read_image(back_image)
    udder_bottom_img = await _read_image(udder_bottom_image)

    side_scale_cm_per_px, side_scale_method = get_scale_cm_per_px(
        side_img, focal_length_mm=focal_length_mm, object_distance_m=object_distance_m, marker_size_cm=marker_size_cm
    )
    back_scale_cm_per_px, back_scale_method = get_scale_cm_per_px(
        back_img, focal_length_mm=focal_length_mm, object_distance_m=object_distance_m, marker_size_cm=marker_size_cm
    )
    udder_scale_cm_per_px, udder_scale_method = get_scale_cm_per_px(
        udder_bottom_img, focal_length_mm=focal_length_mm, object_distance_m=object_distance_m, marker_size_cm=marker_size_cm
    )
    shared_scale_cm_per_px = side_scale_cm_per_px or back_scale_cm_per_px or udder_scale_cm_per_px

    side_det = infer_side(side_img, _SIDE_MODEL)
    scale_side = side_scale_cm_per_px or shared_scale_cm_per_px
    bl_px = side_det.get("length_traits_px", {}).get("body_length", {}).get("total_length_px")
    scale_side = refine_scale(scale_side, bl_px, "body_length")
    if scale_side is None:
        hg_px = side_det.get("length_traits_px", {}).get("heart_girth", {}).get("total_length_px")
        scale_side = refine_scale(scale_side, hg_px, "heart_girth")
    if scale_side is None:
        st_px = side_det.get("length_traits_px", {}).get("stature", {}).get("total_length_px")
        scale_side = refine_scale(scale_side, st_px, "stature")
    side_det["scale_cm_per_px"] = scale_side
    side_det["length_cm"] = convert_length_traits_to_cm(side_det["length_traits_px"], side_det["scale_cm_per_px"])

    back_det = infer_back(back_img, _BACK_MODEL)
    scale_back = back_scale_cm_per_px or shared_scale_cm_per_px
    rw_px = back_det.get("length_traits_px", {}).get("rump_width", {}).get("total_length_px")
    scale_back = refine_scale(scale_back, rw_px, "rump_width")
    back_det["scale_cm_per_px"] = scale_back
    back_det["length_cm"] = convert_back_cm(back_det["length_traits_px"], back_det["scale_cm_per_px"])

    udder_side_det = infer_udder_side(side_img, _UDDER_MODELS)
    scale_udder = udder_scale_cm_per_px or shared_scale_cm_per_px
    udder_bottom_det = infer_udder_bottom(
        udder_bottom_img,
        _UDDER_MODELS,
        cm_per_px=scale_udder,
    )
    tl_px = udder_bottom_det.get("lengths_px", {}).get("front_left")
    scale_udder = refine_scale(scale_udder, tl_px, "teat_length")
    if scale_udder != (udder_scale_cm_per_px or shared_scale_cm_per_px):
        udder_bottom_det = infer_udder_bottom(
            udder_bottom_img,
            _UDDER_MODELS,
            cm_per_px=scale_udder,
        )
        udder_scale_cm_per_px = scale_udder
    else:
        udder_scale_cm_per_px = scale_udder

    traits = compute_all_traits(
        side_results=side_det,
        back_results=back_det,
        udder_side_results=udder_side_det,
        udder_bottom_results=udder_bottom_det,
    )

    metadata = {
        "village_name": village_name,
        "farmer_name": farmer_name,
        "animal_tag": animal_tag,
        "lactation_no": lactation_no,
        "date_of_calving": date_of_calving,
    }
    html_report = render_html_report(traits, metadata)

    overlays = {
        "side": _draw_overlay(
            side_img,
            side_det["keypoints"],
            SIDE_SKELETON_EDGES,
            SIDE_KP_NAMES,
            traits_px=side_det.get("length_traits_px"),
            cm_per_px=side_det.get("scale_cm_per_px"),
        ),
        "back": _draw_overlay(
            back_img,
            back_det["keypoints"],
            BACK_SKELETON_EDGES,
            BACK_KP_NAMES,
            traits_px=back_det.get("length_traits_px"),
            cm_per_px=back_det.get("scale_cm_per_px"),
        ),
        "udder_bottom": _draw_overlay(
            udder_bottom_img,
            udder_bottom_det["keypoints"],
            UDDER_SKELETON_EDGES,
            UDDER_BOTTOM_NAMES,
            traits_px=None,
            cm_per_px=udder_scale_cm_per_px or shared_scale_cm_per_px,
        ),
    }

    return {
        "metadata": metadata,
        "scaling": {
            "side": {"cm_per_px": side_det["scale_cm_per_px"], "method": side_scale_method},
            "back": {"cm_per_px": back_det["scale_cm_per_px"], "method": back_scale_method},
            "udder_bottom": {
                "cm_per_px": udder_scale_cm_per_px or shared_scale_cm_per_px,
                "method": udder_scale_method if udder_scale_cm_per_px else (side_scale_method or back_scale_method),
            },
        },
        "traits": [t.dict() for t in traits],
        "overlays": overlays,
        "html_report": html_report,
    }


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
