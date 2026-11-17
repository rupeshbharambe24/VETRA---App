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
| Side view | YOLO pose | 14 keypoints | `models/side-view/weights/best.pt` |
| Back view | YOLO pose | 10 keypoints | `models/back-view/weights/best.pt` |
| Udder bottom | YOLO pose | 8 keypoints (4 teats, tip + base) | `models/udder-bottom/weights/best.pt` |
| Udder side seg. | U-Net (ResNet34, 1-class, 512px) | binary udder mask | `models/udder-side-seg/udder_seg_best.pth` |
| Udder attachment cls. | ResNet18 (3-class: weak/avg/strong) | attachment quality | `models/udder-side-seg/udder_cls_best.pth` |

The three pose models are YOLOv8n-pose checkpoints trained in [VETRA-v3.0](https://github.com/rupeshbharambe24/VETRA-v3.0) (`args.yaml` next to each checkpoint records the training config). Note: the served side checkpoint has `kpt_shape: [14, 2]` (it is `yolo_pose_side_v1`), while `vetra_backend/config.py` lists 16 side keypoint names — the last two names come from the 16-kp experiment and are never predicted. Training curves, confusion matrices and validation batches are committed alongside the weights, e.g. [`side-view/results.png`](vetra_backend/models/side-view/results.png).

<details>
<summary>Validation metrics (from each model's <code>results.csv</code>, best epoch by pose mAP50-95)</summary>

| Model | Epochs (args.yaml) | Pose precision | Pose recall | Pose mAP50 | Pose mAP50-95 |
|-------|--------------|----------------|-------------|-----------|---------------|
| Side view (14 kp) | 100 | 0.999 | 1.000 | 0.995 | 0.994 |
| Back view (10 kp) | 100 | 0.999 | 1.000 | 0.995 | 0.972 |
| Udder bottom (8 kp) | 80 (74 logged) | 0.888 | 0.923 | 0.893 | 0.694 |

These are scores on the project's own small validation splits; the near-ceiling side/back numbers reflect a small, homogeneous dataset and should not be read as field accuracy. No metrics file is committed for the udder segmentation/classification models.

</details>

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
│   ├── requirements.txt             # backend dependencies
│   ├── docs/
│   │   └── pipeline_overview.md
│   └── models/                      # Trained model weights
│       ├── side-view/
│       ├── back-view/
│       ├── udder-bottom/
│       └── udder-side-seg/
├── vetra-ui/                        # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── pages/                   # TraitExtraction, DataRecords, Schemes, Insurance, Helpline, About, Contact
│   │   ├── components/
│   │   └── lib/, types/
│   └── package.json
├── LICENSE
└── README.md
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
# run from the repository root: the backend is a package with relative imports
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r vetra_backend/requirements.txt

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

## VETRA project map

VETRA (SIH 2025, Grand Finale Top 5) is split across several repositories. ML work evolved v1.1 → v2.0 → v2.2 → v3.0; the apps below consume or capture data for those models.

| Repository | What it is | Stack | Status |
|---|---|---|---|
| [VETRA-v1.1](https://github.com/rupeshbharambe24/VETRA-v1.1) | First ML experiment: 6-keypoint YOLOv8n-pose on side-view cow images + regressors mapping keypoint distances to body measurements (cm) | Python, YOLOv8-pose, scikit-learn | Archived (ML) |
| [VETRA-v2.0](https://github.com/rupeshbharambe24/VETRA-v2.0) | Separate side (10 kp) and back (8 kp) YOLOv8n-pose models, per-measurement pixel-to-cm scaling, measurement extraction, prototype type/breed scoring | Python, Ultralytics | Archived (ML) |
| [VETRA-v2.2-with-app](https://github.com/rupeshbharambe24/VETRA-v2.2-with-app) | v2 pipeline retrained and wrapped in a first FastAPI backend + React UI (`/api/v1/process-image`) | Python, FastAPI, React | Archived (ML + app) |
| [VETRA-v3.0](https://github.com/rupeshbharambe24/VETRA-v3.0) | Final training: side (14 kp), back (10 kp) and udder-bottom (8 kp) YOLOv8n-pose models, udder U-Net + ResNet18, ArUco scaling, dataset tooling | Python, Ultralytics, PyTorch | Final models |
| **[VETRA---App](https://github.com/rupeshbharambe24/VETRA---App)** (this repo) | Final system: FastAPI backend serving the v3.0 pose models + udder U-Net (ResNet34 encoder) and ResNet18 classifier, NDDB-style trait scoring, React web UI | FastAPI, PyTorch, React + Vite | Final (SIH 2025 finale) |
| [vetra-main-app-latest-v3](https://github.com/rupeshbharambe24/vetra-main-app-latest-v3) | Flutter field app: capture protocol, offline SQLite records, PDF reports (not yet wired to the analysis API) | Flutter, Riverpod, SQLite | Prototype |
| [vetra-depth-recorder-latest-v3](https://github.com/rupeshbharambe24/vetra-depth-recorder-latest-v3) | RGB + ARCore depth capture with intrinsics, pose and ZIP export | Flutter, Kotlin, ARCore | Prototype |
| [VETRA---Depth-Recorder](https://github.com/rupeshbharambe24/VETRA---Depth-Recorder) | Earlier capture app: RGB frames + phone-sensor pose metadata (no real depth) | Expo / React Native, TypeScript | Superseded |
| [vetra-pashu-scan](https://github.com/rupeshbharambe24/vetra-pashu-scan) | Early Lovable-generated PWA UI; Supabase edge functions return mock measurements | Vite, React, Supabase | Superseded (UI prototype) |
| [pashudhan-ui](https://github.com/rupeshbharambe24/pashudhan-ui) | Fork of a teammate's Lovable UI prototype (landing page + mock prediction page) | Vite, React | Fork |

## Notes

- Model weight files are committed (~200 MB total). Cloning may take a while.
- The trait ranges and scoring rules are based on NDDB-style scoring but are tunable; thresholds live in `config.py` and `traits.py` for quick iteration.
- This is a **research / prototype** system, not a regulatory-grade animal-evaluation product.

## License

[MIT](LICENSE) © 2025 Rupesh Bharambe
