# VETRA v3.0 – Pipeline Overview

Derived from notebooks in `Training and Processing`.

## Side View (14 keypoints, YOLO pose)
- Checkpoint: `models/side-view/weights/best.pt` (`kpt_shape: [14, 2]`; `load_side_model` refuses a checkpoint whose keypoint count differs from `config.SIDE_KEYPOINT_NAMES`).
- Keypoint order (fixed): hoof_rear_left, hoof_toe_tip_left, hoof_heel_hairline_left, hock_left, stifle_left, hook_left, pin_left, spine_mid_hips, spine_last_rib_top, barrel_last_rib_bottom, shoulder_point, elbow_point, loin_midpoint, udder_floor_centre_rear.
- Skeleton edges: rear hoof→hock/toe/heel, hock→stifle→pin→hook→spine_mid_hips→loin_midpoint→spine_last_rib_top→shoulder→elbow, spine_last_rib_top→barrel_last_rib_bottom→udder_floor_centre_rear plus hock→udder_floor_centre_rear, spine_last_rib_top→elbow, shoulder→pin.
- Length traits (px): stature (spine_mid_hips–hoof), heart_girth (spine_last_rib_top–elbow, x2), body_length (shoulder–pin), body_depth (spine_last_rib_top–barrel_last_rib_bottom, x2), udder_depth (udder_floor_centre_rear to hock & hoof, summed).
- Angle/score traits: rump_angle (hook vs pin vertical), rear_legs_set (hoof→pin vs vertical), foot_angle (hoof/toe/heel angle), angularity (spine_last_rib_top→barrel_last_rib_bottom vs vertical). Udder attachment score injected from udder-side classifier.

## Back View (10 keypoints, YOLO pose)
- Checkpoint: `runs/back_view/yolo_pose_back_v1/weights/best.pt`
- Keypoint order: hoof_rear_left, hoof_rear_right, hock_left, hock_right, pin_left, hook_right, hook_left, pin_right, tail_head, vulva_bottom.
- Skeleton: leg chains (hoof→hock→pin→hook→tail_head) both sides, pin/pin and hook/hook crossbars, tail_head→vulva.
- Length traits (px): rump_width (pins), hook_width (hooks), rear_udder_height proxy (tail_head→vulva_bottom).
- Scores: rump_angle (hooks vs pins y-offset), rear_legs_rear_view (leg angle from vertical), body_condition_score proxy (distance tail_head to hooks/pins).

## Udder Side Segmentation + Attachment Classification
- Segmentation: `udder_seg_best.pth` (Unet resnet34, 1 class, 512px input, sigmoid>0.5 mask).
- Classification: `udder_cls_best.pth` (ResNet18, 3 classes weak/average/strong). ROI = RGB crop around predicted mask with padding, normalized to ImageNet stats, 224px input.
- Output: binary mask + attachment label used for Fore Udder Attachment score (weak=1, avg=5, strong=9).

## Udder Bottom (YOLO pose, 8 keypoints)
- Checkpoint: `runs/udder_bottom_view/yolo_pose_udder_bottom_v1/weights/best.pt`
- Keypoints: front/rear teat tip+base (FL_tip, FL_base, FR_tip, FR_base, RL_tip, RL_base, RR_tip, RR_base).
- Skeleton: tip→base per teat + rectangle linking four bases.
- Measurements: teat lengths (tip→base per teat), placement closeness (base points vs quarter centre, normalized by udder half-width).
- Scores: teat_length (linear 3–9 cm default range), front_teat_placement and rear_teat_placement (closeness 0–1 mapped to 1–9), teat_thickness estimated as 0.2× length (tunable) with linear 1–3.5 cm range.

## Scaling
- Primary: ArUco markers (`DICT_4X4_50`, default physical size 7 cm). Detect via OpenCV ArUco; cm_per_pixel = marker_size_cm / mean_edge_px over all detections.
- If marker missing, results stay in pixels and scoring still runs; cm outputs become `null`.

## Trait Mapping (NDDB-style, current rules)
- Strength: stature, heart girth, body length, body depth (linear cm→score), angularity (angle score).
- Rump: rump angle (side/back score), rump width (pins distance).
- Feet & Leg: rear legs set (side score), rear legs rear view (back score), foot angle (side score).
- Udder: udder depth (side length), fore udder attachment (seg+cls), rear udder height (tail_head→vulva), rear udder width (hook_width proxy), central ligament (placeholder=5), front teat placement, rear teat placement, teat length, teat thickness (udder bottom scores).
- General: body condition score (back proxy).

All ranges/thresholds live in `vetra_backend/config.py` for quick tuning.
