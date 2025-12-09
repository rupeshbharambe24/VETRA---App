from __future__ import annotations

import math
from functools import lru_cache
from typing import Dict, Any

import cv2
import numpy as np
import torch
from torchvision import transforms as T, models
from ultralytics import YOLO
import segmentation_models_pytorch as smp

from . import config
from .scaling import pixel_to_cm


UDDER_BOTTOM_NAMES = config.UDDER_BOTTOM_KEYPOINT_NAMES
U_NAME_TO_IDX = {n: i for i, n in enumerate(UDDER_BOTTOM_NAMES)}
UDDER_SKELETON_EDGES = [
    (U_NAME_TO_IDX["front_left_tip"], U_NAME_TO_IDX["front_left_base"]),
    (U_NAME_TO_IDX["front_right_tip"], U_NAME_TO_IDX["front_right_base"]),
    (U_NAME_TO_IDX["rear_left_tip"], U_NAME_TO_IDX["rear_left_base"]),
    (U_NAME_TO_IDX["rear_right_tip"], U_NAME_TO_IDX["rear_right_base"]),
    (U_NAME_TO_IDX["front_left_base"], U_NAME_TO_IDX["front_right_base"]),
    (U_NAME_TO_IDX["front_right_base"], U_NAME_TO_IDX["rear_right_base"]),
    (U_NAME_TO_IDX["rear_right_base"], U_NAME_TO_IDX["rear_left_base"]),
    (U_NAME_TO_IDX["rear_left_base"], U_NAME_TO_IDX["front_left_base"]),
]


@lru_cache(maxsize=1)
def load_seg_model(device: str | None = None):
    device = device or config.DEFAULT_DEVICE
    model = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=1).to(device)
    state = torch.load(config.UDDER_SEG_MODEL_PATH, map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model


@lru_cache(maxsize=1)
def load_cls_model(device: str | None = None):
    device = device or config.DEFAULT_DEVICE
    model = models.resnet18(pretrained=False)
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, 3)
    state = torch.load(config.UDDER_CLS_MODEL_PATH, map_location=device)
    model.load_state_dict(state)
    model = model.to(device)
    model.eval()
    return model


@lru_cache(maxsize=1)
def load_udder_bottom_model(device: str | None = None) -> YOLO:
    device = device or config.DEFAULT_DEVICE
    model = YOLO(str(config.UDDER_BOTTOM_MODEL_PATH))
    model.to(device)
    return model


def load_udder_models(device: str | None = None) -> Dict[str, Any]:
    return {
        "seg": load_seg_model(device),
        "cls": load_cls_model(device),
        "bottom": load_udder_bottom_model(device),
    }


def segment_image(model, image_bgr: np.ndarray, img_size: int = 512, device: str | None = None):
    device = device or config.DEFAULT_DEVICE
    img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    h, w = img_rgb.shape[:2]
    tf = T.Compose(
        [
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    img_resized = cv2.resize(img_rgb, (img_size, img_size))
    tensor = tf(img_resized).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits)[0, 0].cpu().numpy()
    mask_small = (probs > 0.5).astype("uint8") * 255
    mask = cv2.resize(mask_small, (w, h), interpolation=cv2.INTER_NEAREST)
    return mask


def crop_to_mask(image: np.ndarray, mask: np.ndarray, pad: float = 0.12):
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        return image
    h, w = image.shape[:2]
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    bw, bh = x_max - x_min + 1, y_max - y_min + 1
    pw, ph = int(bw * pad), int(bh * pad)
    x_min, x_max = max(0, x_min - pw), min(w - 1, x_max + pw)
    y_min, y_max = max(0, y_min - ph), min(h - 1, y_max + ph)
    return image[y_min : y_max + 1, x_min : x_max + 1]


def classify_attachment(cls_model, roi_rgb: np.ndarray, device: str | None = None):
    device = device or config.DEFAULT_DEVICE
    label_names = {0: "weak", 1: "average", 2: "strong"}
    tf_cls = T.Compose(
        [
            T.ToPILImage(),
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    tensor = tf_cls(roi_rgb).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = cls_model(tensor)
        pred_idx = int(torch.argmax(logits, dim=1).item())
    return label_names[pred_idx]


def dist(p1, p2):
    return float(np.linalg.norm(np.asarray(p1) - np.asarray(p2)))


def extract_bottom_kpts(res):
    if res.keypoints is None or len(res.keypoints) == 0:
        return None
    return res.keypoints.xy[0].cpu().numpy()


def measure_teat_lengths(kpts, cm_per_px: float | None = None):
    idx = U_NAME_TO_IDX
    vals = {
        "front_left": dist(kpts[idx["front_left_tip"]], kpts[idx["front_left_base"]]),
        "front_right": dist(kpts[idx["front_right_tip"]], kpts[idx["front_right_base"]]),
        "rear_left": dist(kpts[idx["rear_left_tip"]], kpts[idx["rear_left_base"]]),
        "rear_right": dist(kpts[idx["rear_right_tip"]], kpts[idx["rear_right_base"]]),
    }
    if cm_per_px:
        vals = {k: pixel_to_cm(v, cm_per_px) for k, v in vals.items()}
    return vals


def measure_teat_placement_front_rear(kpts):
    idx = U_NAME_TO_IDX
    fl = np.asarray(kpts[idx["front_left_base"]])
    fr = np.asarray(kpts[idx["front_right_base"]])
    rl = np.asarray(kpts[idx["rear_left_base"]])
    rr = np.asarray(kpts[idx["rear_right_base"]])

    centre_L = 0.5 * (fl + rl)
    centre_R = 0.5 * (fr + rr)

    dL_front = abs(fl[0] - centre_L[0])
    dR_front = abs(fr[0] - centre_R[0])
    dL_rear = abs(rl[0] - centre_L[0])
    dR_rear = abs(rr[0] - centre_R[0])

    avg_front = 0.5 * (dL_front + dR_front)
    avg_rear = 0.5 * (dL_rear + dR_rear)

    x_min = min(fl[0], fr[0], rl[0], rr[0])
    x_max = max(fl[0], fr[0], rl[0], rr[0])
    udder_half_width = max((x_max - x_min) / 2.0, 1e-6)

    r_front = min(avg_front / udder_half_width, 1.0)
    r_rear = min(avg_rear / udder_half_width, 1.0)
    return {"front_closeness": 1.0 - r_front, "rear_closeness": 1.0 - r_rear}


def score_from_range(value, lo, hi, reverse=False):
    if lo == hi:
        return 5.0
    t = (value - lo) / (hi - lo)
    t = max(0.0, min(1.0, t))
    if reverse:
        t = 1.0 - t
    return 1.0 + 8.0 * t


def score_teat_length(length_cm: float, species: str = "cattle"):
    if length_cm is None:
        return 5.0
    min_cm, max_cm = config.TRAIT_RANGES_CM.get("teat_length", (3.0, 9.0))
    return score_from_range(length_cm, min_cm, max_cm, reverse=False)


def score_teat_thickness(thickness_cm: float):
    if thickness_cm is None:
        return 5.0
    lo, hi = config.TRAIT_RANGES_CM.get("teat_thickness", (1.0, 3.5))
    return score_from_range(thickness_cm, lo, hi, reverse=False)


def score_teat_placement(closeness: float):
    closeness = max(0.0, min(1.0, closeness))
    return 1.0 + 8.0 * closeness


def infer_udder_side(img_bgr: np.ndarray, models: Dict[str, Any], device: str | None = None):
    device = device or config.DEFAULT_DEVICE
    seg_model = models["seg"]
    cls_model = models["cls"]

    mask = segment_image(seg_model, img_bgr, img_size=512, device=device)
    roi_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    roi_rgb = crop_to_mask(roi_rgb, mask)
    label = classify_attachment(cls_model, roi_rgb, device=device)
    return {"mask": mask, "attachment_label": label}


def infer_udder_bottom(img_bgr: np.ndarray, models: Dict[str, Any], cm_per_px: float | None = None, species: str = "cattle"):
    yolo_model = models["bottom"]
    results = yolo_model(img_bgr, verbose=False)
    res = results[0]
    kpts = extract_bottom_kpts(res)
    if kpts is None:
        raise RuntimeError("No udder bottom keypoints detected.")

    lengths_raw = measure_teat_lengths(kpts, cm_per_px=None)
    lengths_cm = measure_teat_lengths(kpts, cm_per_px=cm_per_px) if cm_per_px else None
    placements = measure_teat_placement_front_rear(kpts)

    ref_teat = "rear_left" if species.lower() == "buffalo" else "front_left"
    teat_length_val_cm = lengths_cm[ref_teat] if lengths_cm else None
    teat_thickness_est = teat_length_val_cm * 0.2 if teat_length_val_cm is not None else None

    scores = {
        "teat_length": float(score_teat_length(teat_length_val_cm, species=species)) if teat_length_val_cm is not None else 5.0,
        "front_teat_placement": float(score_teat_placement(placements["front_closeness"])),
        "rear_teat_placement": float(score_teat_placement(placements["rear_closeness"])),
        "teat_thickness": float(score_teat_thickness(teat_thickness_est)) if teat_thickness_est is not None else 5.0,
    }

    return {
        "keypoints": kpts,
        "lengths_px": lengths_raw,
        "lengths_cm": lengths_cm,
        "placements": placements,
        "scores": scores,
        "teat_length_cm": teat_length_val_cm,
        "teat_thickness_cm": teat_thickness_est,
    }
