from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any

import numpy as np
from pydantic import BaseModel

from . import config


class TraitSection(str, Enum):
    STRENGTH = "Strength"
    RUMP = "Rump"
    FEET_LEG = "Feet and Leg"
    UDDER = "Udder"
    GENERAL = "General"


class TraitResult(BaseModel):
    section: TraitSection
    name: str
    score: int
    measurement_cm: float | None = None
    view: str | None = None
    details: dict | None = None


PLAUSIBLE_CM = {
    "stature": (110.0, 170.0),
    "heart_girth": (120.0, 240.0),
    "body_length": (120.0, 220.0),
    "body_depth": (30.0, 120.0),
    "udder_depth": (-10.0, 50.0),  # allow negative relative to hock
    "rump_width": (8.0, 30.0),
    "rear_udder_height": (5.0, 60.0),
    "rear_udder_width": (8.0, 40.0),
    "teat_length": (2.0, 10.0),
    "teat_thickness": (0.5, 5.0),
}


def sanitize_measurement(trait_key: str, value: float | None) -> float | None:
    if value is None:
        return None
    lo, hi = PLAUSIBLE_CM.get(trait_key, (None, None))
    if lo is None or hi is None:
        return value
    if value < lo * 0.5 or value > hi * 1.5:
        return None
    return value


def assign_linear_score_with_status_jersey(trait_name: str, value: float) -> dict:
    result = {"score": 0, "status": "Undefined"}
    if trait_name == "Stature":
        if value <= 130.0:
            result = {"score": 1, "status": "Very Short"}
        elif value <= 133.0:
            result = {"score": 2, "status": "Short"}
        elif value <= 136.0:
            result = {"score": 3, "status": "Slightly Short"}
        elif value <= 139.0:
            result = {"score": 4, "status": "Intermediate Minus"}
        elif value <= 142.0:
            result = {"score": 5, "status": "Intermediate/Ideal"}
        elif value <= 145.0:
            result = {"score": 6, "status": "Intermediate Plus"}
        elif value <= 148.0:
            result = {"score": 7, "status": "Slightly Tall"}
        elif value <= 151.0:
            result = {"score": 8, "status": "Tall"}
        else:
            result = {"score": 9, "status": "Very Tall"}
    elif trait_name == "Rump Width":
        if value <= 8.0:
            result = {"score": 1, "status": "Very Narrow"}
        elif value <= 9.5:
            result = {"score": 2, "status": "Narrow"}
        elif value <= 11.0:
            result = {"score": 3, "status": "Slightly Narrow"}
        elif value <= 12.5:
            result = {"score": 4, "status": "Intermediate Minus"}
        elif value <= 14.0:
            result = {"score": 5, "status": "Intermediate/Ideal"}
        elif value <= 15.5:
            result = {"score": 6, "status": "Intermediate Plus"}
        elif value <= 17.0:
            result = {"score": 7, "status": "Slightly Wide"}
        elif value <= 18.5:
            result = {"score": 8, "status": "Wide"}
        else:
            result = {"score": 9, "status": "Very Wide"}
    elif trait_name == "Udder Depth":
        if value <= -5.0:
            result = {"score": 1, "status": "Very Deep (Below Hock)"}
        elif value <= -3.0:
            result = {"score": 2, "status": "Deep"}
        elif value <= -1.0:
            result = {"score": 3, "status": "Slightly Deep"}
        elif value <= 1.0:
            result = {"score": 4, "status": "Slightly Below Hock"}
        elif value <= 3.0:
            result = {"score": 5, "status": "At/near Hock"}
        elif value <= 5.0:
            result = {"score": 6, "status": "Slightly Above Hock"}
        elif value <= 7.0:
            result = {"score": 7, "status": "Moderate Above Hock"}
        elif value <= 9.0:
            result = {"score": 8, "status": "Shallow"}
        else:
            result = {"score": 9, "status": "Very Shallow (High)"}
    elif trait_name == "Rump Angle":
        if value >= 0.0:
            result = {"score": 1, "status": "Level/High Pins"}
        elif value >= -2.0:
            result = {"score": 2, "status": "Very Slight Slope"}
        elif value >= -4.0:
            result = {"score": 3, "status": "Slight Slope"}
        elif value >= -6.0:
            result = {"score": 4, "status": "Slightly Ideal Slope"}
        elif value >= -8.0:
            result = {"score": 5, "status": "Ideal Slope"}
        elif value >= -10.0:
            result = {"score": 6, "status": "Slightly Steep"}
        elif value >= -12.0:
            result = {"score": 7, "status": "Steep"}
        elif value >= -14.0:
            result = {"score": 8, "status": "Very Steep"}
        else:
            result = {"score": 9, "status": "Extremely Low Pins"}
    elif trait_name == "Teat Length":
        if value <= 3.0:
            result = {"score": 1, "status": "Very Short"}
        elif value <= 3.5:
            result = {"score": 2, "status": "Short"}
        elif value <= 4.0:
            result = {"score": 3, "status": "Slightly Short"}
        elif value <= 4.5:
            result = {"score": 4, "status": "Intermediate Minus"}
        elif value <= 5.0:
            result = {"score": 5, "status": "Ideal"}
        elif value <= 5.5:
            result = {"score": 6, "status": "Intermediate Plus"}
        elif value <= 6.0:
            result = {"score": 7, "status": "Slightly Long"}
        elif value <= 6.5:
            result = {"score": 8, "status": "Long"}
        else:
            result = {"score": 9, "status": "Very Long"}
    return result
def linear_score_from_range(value_cm: float | None, min_cm: float, max_cm: float, invert: bool = False) -> int:
    if value_cm is None:
        return 0
    if max_cm == min_cm:
        return 5
    t = (value_cm - min_cm) / (max_cm - min_cm)
    t = max(0.0, min(1.0, t))
    if invert:
        t = 1.0 - t
    return int(round(1 + 8 * t))


def _get_measurement(length_cm_dict: Dict[str, Dict[str, float]] | None, key: str):
    if length_cm_dict is None:
        return None
    entry = length_cm_dict.get(key)
    if not entry:
        return None
    return float(entry.get("total_length_cm", None))


def compute_strength_traits_side(side: Dict[str, Any]) -> List[TraitResult]:
    lengths_cm = side.get("length_cm")
    angle_scores = side.get("angle_scores", {})
    res = []
    for trait in ["stature", "heart_girth", "body_length", "body_depth"]:
        value_raw = _get_measurement(lengths_cm, trait)
        value = sanitize_measurement(trait, value_raw)
        name_readable = trait.replace("_", " ").title()
        if value is not None and name_readable in {"Stature"}:
            scored = assign_linear_score_with_status_jersey(name_readable, value)
            res.append(
                TraitResult(
                    section=TraitSection.STRENGTH,
                    name=name_readable,
                    score=int(scored["score"]),
                    measurement_cm=value,
                    view="side",
                    details={"status": scored["status"]},
                )
            )
        else:
            lo, hi = config.TRAIT_RANGES_CM.get(trait, (0.0, 1.0))
            res.append(
                TraitResult(
                    section=TraitSection.STRENGTH,
                    name=name_readable,
                    score=linear_score_from_range(value, lo, hi),
                    measurement_cm=value,
                    view="side",
                )
            )
    # Angularity from angle score if present
    ang = angle_scores.get("angularity")
    if ang:
        res.append(
            TraitResult(
                section=TraitSection.STRENGTH,
                name="Angularity",
                score=int(ang["score"]),
                measurement_cm=None,
                view="side",
                details={"angle_deg": ang.get("angle_deg")},
            )
        )
    return res


def compute_rump_traits(side: Dict[str, Any], back: Dict[str, Any]) -> List[TraitResult]:
    res = []
    # Rump angle (prefer side; fallback back)
    candidate = side.get("angle_scores", {}).get("rump_angle") if side else None
    if candidate is None and back:
        candidate = back.get("angle_scores", {}).get("rump_angle")
    if candidate:
        score = int(candidate["score"])
        if "angle_deg" in candidate:
            scored = assign_linear_score_with_status_jersey("Rump Angle", float(candidate["angle_deg"]))
            score = int(scored["score"])
        res.append(
            TraitResult(
                section=TraitSection.RUMP,
                name="Rump Angle",
                score=score,
                measurement_cm=None,
                view="side" if side else "back",
                details={"dy_px": candidate.get("dy_px"), "status": scored["status"] if "scored" in locals() else None},
            )
        )
    # Rump width from back pins
    rump_width_cm = sanitize_measurement("rump_width", _get_measurement(back.get("length_cm") if back else None, "rump_width"))
    if rump_width_cm is not None:
        scored = assign_linear_score_with_status_jersey("Rump Width", rump_width_cm)
        res.append(
            TraitResult(
                section=TraitSection.RUMP,
                name="Rump Width",
                score=int(scored["score"]),
                measurement_cm=rump_width_cm,
                view="back",
                details={"status": scored["status"]},
            )
        )
    return res


def compute_feet_leg_traits(side: Dict[str, Any], back: Dict[str, Any]) -> List[TraitResult]:
    res = []
    for name, pretty in [
        ("rear_legs_set", "Rear Legs Set"),
        ("foot_angle", "Foot Angle"),
    ]:
        sc = side.get("angle_scores", {}).get(name) if side else None
        if sc:
            res.append(
                TraitResult(
                    section=TraitSection.FEET_LEG,
                    name=pretty,
                    score=int(sc["score"]),
                    measurement_cm=None,
                    view="side",
                )
            )
    rear_view = back.get("angle_scores", {}).get("rear_legs_rear_view") if back else None
    if rear_view:
        res.append(
            TraitResult(
                section=TraitSection.FEET_LEG,
                name="Rear Legs Rear View",
                score=int(rear_view["score"]),
                measurement_cm=None,
                view="back",
            )
        )
    return res


def compute_udder_traits(side: Dict[str, Any], back: Dict[str, Any], udder_side: Dict[str, Any], udder_bottom: Dict[str, Any]) -> List[TraitResult]:
    res = []
    udder_depth = sanitize_measurement("udder_depth", _get_measurement(side.get("length_cm") if side else None, "udder_depth"))
    if udder_depth is not None:
        scored = assign_linear_score_with_status_jersey("Udder Depth", udder_depth)
        res.append(
            TraitResult(
                section=TraitSection.UDDER,
                name="Udder Depth",
                score=int(scored["score"]),
                measurement_cm=udder_depth,
                view="side",
                details={"status": scored["status"]},
            )
        )
    else:
        res.append(
            TraitResult(
                section=TraitSection.UDDER,
                name="Udder Depth",
                score=linear_score_from_range(udder_depth, *config.TRAIT_RANGES_CM.get("udder_depth", (20.0, 60.0))),
                measurement_cm=udder_depth,
                view="side",
            )
        )

    # Fore udder attachment from classifier label
    if udder_side and udder_side.get("attachment_label"):
        label = udder_side["attachment_label"].lower()
        mapping = {"weak": 1, "average": 5, "avg": 5, "strong": 9}
        res.append(
            TraitResult(
                section=TraitSection.UDDER,
                name="Fore Udder Attachment",
                score=mapping.get(label, 5),
                measurement_cm=None,
                view="udder_side",
            )
        )

    # Rear udder height from back
    rear_ud_height = sanitize_measurement("rear_udder_height", _get_measurement(back.get("length_cm") if back else None, "rear_udder_height"))
    lo, hi = config.TRAIT_RANGES_CM.get("rear_udder_height", (10.0, 45.0))
    res.append(
        TraitResult(
            section=TraitSection.UDDER,
            name="Rear Udder Height",
            score=linear_score_from_range(rear_ud_height, lo, hi),
            measurement_cm=rear_ud_height,
            view="back",
        )
    )

    # Rear udder width proxy from hook width
    rear_ud_width = sanitize_measurement("rear_udder_width", _get_measurement(back.get("length_cm") if back else None, "hook_width"))
    lo, hi = config.TRAIT_RANGES_CM.get("rear_udder_width", (25.0, 55.0))
    res.append(
        TraitResult(
            section=TraitSection.UDDER,
            name="Rear Udder Width",
            score=linear_score_from_range(rear_ud_width, lo, hi),
            measurement_cm=rear_ud_width,
            view="back",
        )
    )

    # Udder bottom traits
    if udder_bottom:
        scores = udder_bottom.get("scores", {})
        res.append(
            TraitResult(
                section=TraitSection.UDDER,
                name="Front Teat Placement",
                score=int(round(scores.get("front_teat_placement", 0))),
                measurement_cm=None,
                view="udder_bottom",
            )
        )
        res.append(
            TraitResult(
                section=TraitSection.UDDER,
                name="Rear Teat Placement",
                score=int(round(scores.get("rear_teat_placement", 0))),
                measurement_cm=None,
                view="udder_bottom",
            )
        )
        teat_len = sanitize_measurement("teat_length", udder_bottom.get("teat_length_cm", None))
        teat_thk = sanitize_measurement("teat_thickness", udder_bottom.get("teat_thickness_cm", None))
        if teat_len is not None:
            scored_len = assign_linear_score_with_status_jersey("Teat Length", teat_len)
        else:
            scored_len = {"score": scores.get("teat_length", 5), "status": None}
        res.append(
            TraitResult(
                section=TraitSection.UDDER,
                name="Teat Length",
                score=int(round(scored_len["score"])),
                measurement_cm=teat_len,
                view="udder_bottom",
                details={"status": scored_len["status"]},
            )
        )
        res.append(
            TraitResult(
                section=TraitSection.UDDER,
                name="Teat Thickness",
                score=int(round(scores.get("teat_thickness", 0))),
                measurement_cm=teat_thk,
                view="udder_bottom",
            )
        )

    # Central ligament placeholder
    res.append(
        TraitResult(
            section=TraitSection.UDDER,
            name="Central Ligament",
            score=5,
            measurement_cm=None,
            view="udder_bottom",
        )
    )
    return res


def compute_general_traits(side: Dict[str, Any], back: Dict[str, Any]) -> List[TraitResult]:
    res = []
    bcs = None
    if back and back.get("angle_scores", {}).get("body_condition_score"):
        bcs = int(back["angle_scores"]["body_condition_score"]["score"])
    res.append(
        TraitResult(
            section=TraitSection.GENERAL,
            name="Body Condition Score",
            score=bcs if bcs is not None else 5,
            measurement_cm=None,
            view="back" if bcs is not None else None,
        )
    )
    return res


def compute_all_traits(
    side_results: Dict[str, Any] | None,
    back_results: Dict[str, Any] | None,
    udder_side_results: Dict[str, Any] | None,
    udder_bottom_results: Dict[str, Any] | None,
) -> List[TraitResult]:
    traits: List[TraitResult] = []
    side = side_results or {}
    back = back_results or {}
    udder_side = udder_side_results or {}
    udder_bottom = udder_bottom_results or {}

    traits.extend(compute_strength_traits_side(side))
    traits.extend(compute_rump_traits(side, back))
    traits.extend(compute_feet_leg_traits(side, back))
    traits.extend(compute_udder_traits(side, back, udder_side, udder_bottom))
    traits.extend(compute_general_traits(side, back))

    # clamp scores to 1-9
    for t in traits:
        t.score = max(1, min(9, int(t.score)))
    return traits
