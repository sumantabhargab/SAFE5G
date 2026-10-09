# SAFE5G — Project Context

**Last updated:** 2026-10-09

## What SAFE5G is

SAFE5G ("Safe 5G") is an AI-based women-safety surveillance prototype developed during a
one-month summer internship (01/07/2026 – 30/07/2026) at the **5G Use Case Laboratory,
Dept. of EEE, IIT Guwahati**, sponsored by the Department of Telecommunications (DoT),
Government of India.

- **Developer:** Sumanta Bhargab (B.Tech CSE, Jorhat Engineering College, Roll 9395067004)
- **Collaborator:** Atlanta Gogoi (B.Tech ECE, DUIET, Roll ECE 24-07)
- **Supervisor:** Dr. A. Rajesh, Assoc. Professor, EEE, IIT Guwahati
- **Report also credits:** Dr. Salil Kashyap, Assoc. Professor, EEE, IIT Guwahati
- **Repo:** https://github.com/sumantabhargab/SAFE5G.git (cloned at `D:\academic internship\SAFE5G`)
- **Deliverables on disk:** `D:\academic internship\report sumanta.pdf`, `report atlanta.pdf` (12-page internship reports), `presentation.pdf` (12 slides, image-only, no text layer — pages rendered to `ppt_pages/` for viewing)

## The idea / objective

CCTV today is passive: it records but doesn't understand. SAFE5G watches live video and
automatically detects emergencies **without anyone pressing a button**:

1. **Distress HELP gesture** — victim raises an open palm (MediaPipe Hands, 21 landmarks).
   Core premise: a victim who cannot speak or shout can still raise a hand.
2. **Violence detection** — identify violent activity in the scene.
3. **Person/vehicle detection** — YOLOv8n for situational awareness.

On detection: save snapshot → log incident to SQLite → fire SOS escalation
(SMS/email/webhook) → show on live Flask dashboard with threat levels and alert history.

The "5G" in the name = future deployment context (edge AI + 5G ultra-low-latency emergency
notification in smart cities), not something implemented today.

## Tech stack (pinned in requirements.txt)

Python, Flask 3.1.1, OpenCV 4.10, ultralytics 8.3.189 (YOLOv8n), MediaPipe 0.10.21,
PyTorch 2.4.1, EfficientNet-B0 (timm), SQLite (stdlib), ONNX runtime. Frontend:
HTML/CSS/JS single stylesheet, three Jinja templates, MJPEG live stream.

## Architecture as it actually runs

```
run.py ──► camera_manager (cv2 capture, singleton) ──► ai/pipeline.AIPipeline.process(frame)
        │                                              ├─ yolo_detector  (YOLOv8n, persons/vehicles)
        │                                              ├─ gesture_detector (MediaPipe open palm = HELP)
        │                                              ├─ violence_detector (frame diff — PLACEHOLDER)
        │                                              ├─► sensors.sos_trigger → alert_manager → SQLite
        │                                              └─► media_manager (snapshots, recording)
        └──► web/app.py (Flask, port 5000): MJPEG /video_feed + 3 pages + 3 mock API routes
```

## Module-by-module state (full-depth analysis, 2026-10-09)

### Active path
- `run.py` — entry: Flask on daemon thread + camera loop. Hardcoded "Camera 01"/"Main Gate",
  no error recovery on dropped frames.
- `camera/camera_manager.py` — singleton, `update_frame()`/`get_jpeg()` for MJPEG.
  `generate_frames()` busy-spins when no frame (CPU burn), no lock around latest_frame.
- `ai/yolo_detector.py` — the real detector. cwd-relative model path `models/yolov8n.pt`
  (breaks unless run from root); loads model at import; duplicate FPS HUD vs pipeline;
  "confidence" = max over ALL classes incl. vehicles (wrong semantics for alerts).
- `ai/gesture_detector.py` — MediaPipe open-palm = HELP. Bugs: thumb logic only correct for
  right hands; fails on rotated hands; any open palm (waving) = SOS; private mediapipe
  import path; loads model at import.
- `ai/violence_detector.py` — **frame-differencing motion detection, NOT violence**.
  Any camera shake/lighting change triggers. Placeholder.
- `ai/pipeline.py` — orchestrator. Triple frame.copy() per frame, no SOS debounce/cooldown,
  hardcoded recording FPS 20, recording never stops while threat persists.
- `sensors/alert_manager.py` — alerts → SQLite + snapshot + winsound beep (**Windows-only
  import**), observer pattern, no dedup/throttle, time has no date/timezone.
- `sensors/sos_trigger.py` — SMS/email are print-stubs; only webhook is real; frame passed
  but never attached; 3 new daemon threads per alert, no cooldown.
- `web/app.py` — MJPEG stream works; `/api/status`, `/api/threat`, `/api/modules` are
  **fully hardcoded** (`alerts: 31`, fps 30, threat 23); `debug=True` on `0.0.0.0`
  (security issue); busy-wait in frame generator.
- `web/static/js/app.js` (625 lines) — **dashboard simulation**: fake incidents generated
  with Math.random() every 10 s; frontend never calls any /api endpoint.
- `database/database.py` — SQLite wrapper, parameterized queries (good). Single shared
  connection, `check_same_thread=False`, no locking → races between Flask threads and
  pipeline. CWD-relative path, instantiated at import. **Never used by the web app** —
  alerts page is static HTML.
- `media/save_media.py`, `media/report_generator.py` — snapshot/recording manager, TXT/CSV/JSON
  report generator. Minor issues only (stop_recording returns None if never started; same-second
  filename collisions).

### Dead code (exists, never wired into the running path)
- `rules/rule_engine.py` — the best-designed module: temporal threat scoring, debouncing
  (±2 gesture / ±1 violence), weighted score, EMA smoothing, threat levels SAFE→CRITICAL,
  10 s alert cooldown. **Disconnected.** Has a scale-mismatch bug if wired naively: expects
  0–100 confidences, pipeline passes 0–1 floats.
- `rules/zones.py` — polygon restricted zones; **broken** (int32 contour crashes
  pointPolygonTest; pointless UMat wrap); hardcoded 900–1250px coords; unused.
- `rules/weights.json` — rule weights (panic 100, shake 50, tampering 40, following 25,
  loitering 20, night 10 …) read by nothing; those rules don't exist in code.
- `ai/tracker.py` + `ai/detector.py` + `ai/person.py` + `ai/detection.py` — ByteTrack
  multi-person tracking stack, unused by pipeline; tracker never prunes lost tracks;
  would load a 2nd/3rd YOLO instance.
- `camera/webcam.py` — dead camera abstraction; its `import config` doesn't resolve → would
  crash if imported.
- `ai/models/violence_classifier.pth` — **the trained model, orphaned**. Never loaded.
- `utils/logger.py` — empty stub. `utils/geometry.py` duplicates `utils/helpers.py` distance().

### Bugs that break or mislead
1. **Leaked Kaggle API key** in `notebook1.ipynb` cell 2 (plaintext). **Must revoke.**
2. `utils/drawing.py` calls `config.GREEN/RED/YELLOW/BLUE` — don't exist in config.py
   (only a `COLORS` dict) → AttributeError on first draw.
3. Bare `import config` in several modules; correct form is `from utils import config`.
4. YOLO path: yolo_detector says `models/yolov8n.pt`, config says `ai/models/`, README says
   `models/`; README says `violence.keras` but actual artifact is `violence_classifier.pth`.
   Root also has a duplicate `yolov8n.pt` committed.
5. MJPEG busy-spin in both `app.py` and `camera_manager.py`.
6. SQLite thread races (see above).
7. No alert cooldown in the live path → sustained detection floods disk/DB + threads.
8. requirements.txt has a UTF-8 BOM; TF+Keras+Torch+mediapipe+ultralytics all at once (~5 GB);
   numpy 1.26 incompatible with the Python 3.14 that produced the committed `__pycache__`.
9. `filename()` in helpers uses whole-second timestamps → same-second overwrites;
   `cv2.imwrite` return value ignored.
10. Committed junk: `__pycache__/`, notebooks with error outputs, big embedded figures.

## ML training (notebooks)

- `notebook1.ipynb` (complete): Kaggle "Real Life Violence Situations Dataset"
  (mohamedmustafa, 3.58 GB, 1000+1000 videos) → every-10th-frame extraction, Laplacian
  sharpness filter >120 → 20,865 frames, 80/10/10 split (no video leakage) →
  **EfficientNet-B0 (timm), Adam 1e-4, AMP, 10 epochs** → test **Acc 0.9636, F1 0.9530**.
  Caveats: frame-level near-duplicates inflate metrics; class imbalance from sharpness
  filter (7255 vs 9827 train) unhandled. Saves `violence_classifier.pth`.
- `02_train_model_ipynb.ipynb` (v2, **unfinished**): Drive-mounted retrain, 25 epochs +
  early stopping, RandomAffine augmentation — config/data wiring done, no training/eval
  cells. Has stale paths, duplicate cells, error outputs.
- Format mismatch: README says `violence.keras`; actual artifact is `.pth` (PyTorch).

## Presentation / report framing

Title: "Safe5G: A Multi-Modal AI-Based Smart Surveillance Framework for Real-Time Threat
Detection and Emergency Notification". Presentation = 12 slides, image-only PDF.
Reports claim the system "successfully" detects violence + gestures — currently only the
gesture path and YOLO are genuinely functional; violence path is a placeholder and the
dashboard shows simulated data. Presentation strategy agreed with Sumanta: **make every
claim demonstrable before presenting** — wire the real trained model, connect dashboard to
real data, fix gesture reliability. Narrative: problem → multi-modal solution → working
prototype → 5G/edge future scope.

## Agreed next steps (priority order)

1. ~~Revoke Kaggle key + scrub from notebook~~ (user action: revoke at kaggle.com; scrub
   from notebook + git history)
2. Fix crashers: config color constants, bare imports, YOLO model path
3. Wire `violence_classifier.pth` into pipeline (replace motion detection)
4. Connect web dashboard + /api endpoints to real SQLite data; alerts page from DB
5. Wire RuleEngine (fix 0–100 vs 0–1 scale) for threat scoring + cooldown
6. Security/robustness: debug=False, MJPEG throttle + sleep, SQLite WAL + lock, alert cooldown
7. Gesture fix: handedness-aware thumb logic, temporal smoothing
8. Cleanup: delete dead code (or wire it), remove committed binaries/pycache, fix README paths

## Decisions & preferences

- Full-depth analysis done via 5 parallel agents; reports/presentation read from
  `D:\academic internship` (not in repo).
- Sumanta wants the project presented honestly as a women-safety system, with the demo
  defensible under examiner questioning.
- A PRD for the final product is being written alongside this file.
