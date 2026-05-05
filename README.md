# VETRA — Visual Evaluation of Traits & Reproductive Anatomy

An AI-based **type-classification system for cattle and buffaloes** that turns three smartphone photos (side / back / udder-bottom) into a structured set of physical traits, NDDB-style scores, and a printable report.

Built for **SIH 2025 Grand Finale (Top 5)** under the Ministry of Fisheries, Animal Husbandry & Dairying.

## What it does

Given three uploaded images of an animal:

1. **Detects keypoints** with three custom-trained YOLO pose models (side / back / udder-bottom) and a U-Net + ResNet18 udder classifier.
2. **Computes physical scale** in cm/pixel by detecting ArUco markers in the images (with a pinhole-camera fallback when no marker is found).
3. **Derives 18+ NDDB-style traits** across Strength, Rump, Feet & Leg, Udder, and General sections — including stature, heart girth, body length, rump width, udder depth, teat placements, teat length, fore-udder attachment, and more.
4. **Returns** a structured JSON of trait scores + matplotlib overlays + a generated HTML report.

## Models

| View | Architecture | Output | Checkpoint |
|------|-------------|--------|-----------|
| Side view | YOLO pose | 16 keypoints | `models/side-view/weights/best.pt` |
| Back view | YOLO pose | 10 keypoints | `models/back-view/weights/best.pt` |
| Udder bottom | YOLO pose | 8 keypoints (4 teats, tip + base) | `models/udder-bottom/weights/best.pt` |
| Udder side seg. | U-Net (ResNet34, 1-class, 512px) | binary udder mask | `models/udder-side-seg/udder_seg_best.pth` |
| Udder attachment cls. | ResNet18 (3-class: weak/avg/strong) | attachment quality | `models/udder-side-seg/udder_cls_best.pth` |

### Side keypoints (16)
`hoof_rear, hoof_toe_tip, hoof_heel_hairline, hock, stifle, hook, pin, spine_last_rib_top, barrel_last_rib_bottom, withers, shoulder_point, elbow_point, front_hoof, abdomen_girth, abdomen_body_depth, udder_bottom`

### Back keypoints (10)
`hoof_rear_left/right, hock_left/right, pin_left/right, hook_left/right, tail_head, vulva_bottom`

### Udder-bottom keypoints (8)
`FL_tip, FL_base, FR_tip, FR_base, RL_tip, RL_base, RR_tip, RR_base` (front/rear left/right teat, tip + base)

## Trait Pipeline

| Section | Traits |
|---------|--------|
| **Strength** | stature, heart girth, body length, body depth, angularity |
| **Rump** | rump angle (side + back), rump width |
| **Feet & Leg** | rear legs set, rear legs rear-view, foot angle |
| **Udder** | udder depth, fore-udder attachment (seg+cls), rear-udder height, rear-udder width, central ligament, front teat placement, rear teat placement, teat length, teat thickness |
| **General** | body condition score |

Linear traits in cm are mapped to NDDB 1–9 scores via tunable ranges in `vetra_backend/config.py`. Angular traits use angle-from-vertical scores. The udder attachment classifier maps `weak/average/strong → 1/5/9`.

Full pipeline details are in [`vetra_backend/docs/pipeline_overview.md`](vetra_backend/docs/pipeline_overview.md).

## ArUco Scaling

- Default dictionary: `DICT_4X4_50`, marker physical size: 7.0 cm (configurable per-request).
- `cm_per_pixel = marker_size_cm / mean_edge_px` over all detected markers.
- Pinhole-camera fallback uses `focal_length_mm` + `object_distance_m` if no marker is detected.
- If both fail, results stay in pixels and cm outputs become `null` (scores still run).

## API

`POST /api/v1/analyze` (multipart form):

| Field | Type | Required | Description |
|-------|------|---------|-------------|
| `side_image` | file | yes | Side-view image |
| `back_image` | file | yes | Back-view image |
| `udder_bottom_image` | file | yes | Udder-bottom image |
| `village_name`, `farmer_name`, `animal_tag`, `lactation_no`, `date_of_calving` | str | optional | Metadata for the report |
| `focal_length_mm`, `object_distance_m` | float | optional | Pinhole fallback for scaling |
| `marker_size_cm` | float | optional | Override default marker size |

Returns: per-view keypoints, computed traits (px and cm), section scores, base64 overlay images, and an HTML report.

`GET /api/v1/health` — health check.

## Project Structure

```
VETRA---App/
├── vetra_backend/                   # FastAPI backend
│   ├── api_main.py                  # /api/v1/analyze, /api/v1/health
│   ├── config.py                    # Model paths, keypoint names, scaling defaults
│   ├── models_side.py               # Side-view inference + skeleton + length traits
│   ├── models_back.py               # Back-view inference + skeleton + length traits
│   ├── models_udder.py              # Udder bottom (pose) + side (seg + cls)
│   ├── scaling.py                   # ArUco detection + pinhole fallback
│   ├── traits.py                    # Trait computation + NDDB-style scoring
│   ├── reporting.py                 # HTML report generator
│   ├── docs/
│   │   └── pipeline_overview.md
│   └── models/                      # Trained model weights
│       ├── side-view/
│       ├── back-view/
│       ├── udder-bottom/
│       └── udder-side-seg/
└── vetra-ui/                        # React + Vite + Tailwind frontend
    ├── src/
    │   ├── pages/                   # TraitExtraction, DataRecords, Schemes, Insurance, Helpline, About, Contact
    │   ├── components/
    │   ├── lib/, types/
    └── package.json
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Uvicorn, Pydantic |
| Detection / Pose | Ultralytics YOLO (custom-trained) |
| Segmentation | PyTorch (U-Net ResNet34) |
| Classification | PyTorch (ResNet18) |
| CV | OpenCV (ArUco), NumPy, Pillow |
| Reporting | Matplotlib overlays + HTML report |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, react-i18next, jsPDF |

## Setup

### Backend

```bash
cd vetra_backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install fastapi uvicorn pydantic ultralytics torch torchvision opencv-contrib-python numpy matplotlib pillow

uvicorn vetra_backend.api_main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd vetra-ui
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Related Repositories

- [vetra-main-app-latest-v3](https://github.com/rupeshbharambe24/vetra-main-app-latest-v3) — Flutter mobile companion app (field capture, offline records, PDF reports)
- [vetra-depth-recorder-latest-v3](https://github.com/rupeshbharambe24/vetra-depth-recorder-latest-v3) — ARCore Depth API prototype (RGB + depth capture)

## Notes

- Model weight files are committed (~200 MB total). Cloning may take a while.
- The trait ranges and scoring rules are based on NDDB-style scoring but are tunable; thresholds live in `config.py` and `traits.py` for quick iteration.
- This is a **research / prototype** system, not a regulatory-grade animal-evaluation product.
