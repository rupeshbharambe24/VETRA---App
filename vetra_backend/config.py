import torch
from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = Path(__file__).resolve().parent

# Local model directory (new layout under vetra_backend/models)
MODEL_DIR = BACKEND_ROOT / "models"

# Camera defaults (for pinhole fallback)
SENSOR_WIDTH_MM = 6.4  # approximate phone sensor width; adjust per device

# Device selection
DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Model checkpoints (update paths here if you retrain)
SIDE_MODEL_PATH = MODEL_DIR / "side-view" / "weights" / "best.pt"
BACK_MODEL_PATH = MODEL_DIR / "back-view" / "weights" / "best.pt"
UDDER_BOTTOM_MODEL_PATH = MODEL_DIR / "udder-bottom" / "weights" / "best.pt"
UDDER_SEG_MODEL_PATH = MODEL_DIR / "udder-side-seg" / "udder_seg_best.pth"
UDDER_CLS_MODEL_PATH = MODEL_DIR / "udder-side-seg" / "udder_cls_best.pth"

# ArUco scaling defaults
ARUCO_DICT_NAME = "DICT_4X4_50"
DEFAULT_MARKER_SIZE_CM = 7.0  # physical side length of printed marker (adjust to match yours)

# Side view 16-kp order (must stay consistent with training)
SIDE_KEYPOINT_NAMES = [
    "hoof_rear",            # 0
    "hoof_toe_tip",         # 1
    "hoof_heel_hairline",   # 2
    "hock",                 # 3
    "stifle",               # 4
    "hook",                 # 5
    "pin",                  # 6
    "spine_last_rib_top",   # 7
    "barrel_last_rib_bottom",  # 8
    "withers",              # 9
    "shoulder_point",       # 10
    "elbow_point",          # 11
    "front_hoof",           # 12
    "abdomen_girth",        # 13
    "abdomen_body_depth",   # 14
    "udder_bottom",         # 15
]

# Back view 10-kp order (matches train-back.ipynb mapping)
BACK_KEYPOINT_NAMES = [
    "hoof_rear_left",   # 0
    "hoof_rear_right",  # 1
    "hock_left",        # 2
    "hock_right",       # 3
    "pin_left",         # 4
    "hook_right",       # 5
    "hook_left",        # 6
    "pin_right",        # 7
    "tail_head",        # 8
    "vulva_bottom",     # 9
]

# Udder bottom 8-kp order
UDDER_BOTTOM_KEYPOINT_NAMES = [
    "front_left_tip",
    "front_left_base",
    "front_right_tip",
    "front_right_base",
    "rear_left_tip",
    "rear_left_base",
    "rear_right_tip",
    "rear_right_base",
]

# Trait scoring rough ranges (tunable; cm values assume adult cows)
TRAIT_RANGES_CM = {
    "stature": (110.0, 160.0),
    "heart_girth": (150.0, 220.0),
    "body_length": (120.0, 190.0),
    "body_depth": (40.0, 90.0),
    "udder_depth": (20.0, 60.0),
    "rump_width": (25.0, 55.0),
    "rear_udder_height": (10.0, 45.0),
    "rear_udder_width": (25.0, 55.0),
    "teat_length": (3.0, 9.0),
    "teat_thickness": (1.0, 3.5),
}

# Default report metadata labels (used in API responses)
REPORT_META_FIELDS = [
    "village_name",
    "farmer_name",
    "animal_tag",
    "lactation_no",
    "date_of_calving",
]
