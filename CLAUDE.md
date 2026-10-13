# SAFE5G — Project Reference

## What this is

Safe5G is a real-time multi-sensor threat detection and alerting system for campus/public safety. It runs from a live camera feed and a web dashboard with video upload analysis. It combines three AI models with a rule-based threat engine:

- **YOLOv8n** — person/vehicle detection + ReID tracking
- **EfficientNet-B0** — frame-level violence classifier (trained on Real Life Violence Situations dataset)
- **MediaPipe Hand Landmarker** — HELP gesture detection (open palm, 5-finger)
- **Rule Engine** — fuses all signals into threat score + alert firing

## Architecture

```
Camera Feed → YOLO → Gesture → Violence → RuleEngine → Alert/Recording → HUD overlay
                   │                                    │
                   └── Person tracking (ReID) ──────────┘
                                                         │
                                            Flask Web Dashboard (/upload analysis)
```

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Entry point — starts camera loop + Flask dashboard |
| `ai/pipeline.py` | Per-frame orchestrator — calls YOLO, gesture, violence, rule engine |
| `ai/yolo_detector.py` | YOLOv8n person/vehicle detection + ReID tracker |
| `ai/violence_detector.py` | EfficientNet-B0 violence classifier with sliding-window temporal voting |
| `ai/gesture_detector.py` | MediaPipe hand landmarker — HELP gesture (open palm) detection |
| `ai/tracker.py` | ReID person track manager |
| `rules/rule_engine.py` | Threat scoring + alert gating (score ≥ 75 → trigger) |
| `sensors/sos_trigger.py` | Alert dispatch (webhook, SMS, email) |
| `sensors/alert_manager.py` | AlertManager — per-type cooldown, persistence, resolution |
| `camera/camera_manager.py` | Camera source manager |
| `database/database.py` | SQLite alert database (SQLiteDict-backed) |
| `media/save_media.py` | Recording + report generation |
| `web/app.py` | Flask app — dashboard, MJPEG stream, upload analysis |
| `utils/config.py` | All configuration constants |
| `utils/helpers.py` | Drawing, banner overlay utilities |
| `utils/logger.py` | Structured logger |

## Configuration (utils/config.py)

| Constant | Default | Notes |
|----------|---------|-------|
| `VIOLENCE_THRESHOLD` | 0.70 | Frame-level violence probability threshold |
| `VIOLENCE_WINDOW` | 16 | Sliding window size (frames) |
| `VIOLENCE_WINDOW_VOTES` | 8 | Votes needed in window to fire violence flag |
| `Yolo_CONFIDENCE` | 0.40 | YOLO confidence threshold |
| `GESTURE_CONFIRM_FRAMES` | 5 | Consecutive frames of palm needed for HELP gesture |
| `ALERT_COOLDOWN` | 60s | Per-type cooldown between alerts |
| `CAMERA_INDEX` | 2 | Video capture device index |
| `FPS` | 15 | Camera capture FPS |

## Violence Classifier Details

- **Model**: EfficientNet-B0, 2 classes (NonViolence=0, Violence=1)
- **Training**: Trained on Real Life Violence Situations dataset (ImageFolder with train/val/test splits under `Safe5G_Frames/`)
- **Training transforms**: Resize(224), RandomHorizontalFlip, RandomRotation(10), RandomAffine, ColorJitter
- **Test-time**: Resize(224) + ImageNet normalization (no augmentation)
- **Input**: Single frame → 224x224 → classifier → P(violence)
- **Temporal**: Sliding window of 16 frames, requires ≥8 votes above threshold
- **Performance**: Tested F1 ~0.953 on Real Life Violence Situations dataset
- **Model file**: `ai/models/violence_classifier.pth`

## Rules / Threat Scoring

The RuleEngine (`rules/rule_engine.py`) computes a score 0-100:

- SOS Gesture (palm held ≥15 frames): +45 points
- Violence (detected in ≥10 frames): +25 points
- Violence confidence tiers: +10 if ≥90%, +7 if ≥80%
- Person count tiers: +5 (2+), +8 (3+), +10 (5+)
- Vehicle tiers: +2 (1+), +5 (3+)
- Persistent gesture (≥25 frames): +10 bonus
- Smoothed with EMA (0.75 previous + 0.25 current)

Threat levels: SAFE (<30), LOW (<50), MEDIUM (<70), HIGH (<90), CRITICAL (≥90)
Trigger: score ≥ 75

## Running

```bash
cd SAFE5G
pip install -r requirements.txt
python run.py
```

Dashboard runs at `http://127.0.0.1:5000`
- `/` — live dashboard with camera stream
- `/upload` — upload video for offline analysis
- `/alerts` — alert history
- `/cameras` — camera status page

## Video Upload Analysis

The `/upload` POST endpoint accepts MP4/AVI/MOV/MKV/FLV/WMV. It spawns a background thread that:
1. Reads every frame, downscales to 480px width
2. Runs YOLO + violence classifier + gesture detection per frame
3. Coalesces consecutive violent/gesture frames into timeline events
4. Writes annotated output video to `media/analysis_output/`
5. Returns summary via `/api/video/status/<id>`

## Key Pipelines

### Live Camera (`run.py` → `pipeline.process`)
Every frame from `cv2.VideoCapture(CAMERA_INDEX)`:
1. YOLO detects persons/vehicles → tracks with ReID
2. Gesture detector checks for HELP gesture
3. Violence classifier runs on the frame with sliding window
4. RuleEngine fuses all signals → threat level
5. If trigger fires → dispatch alert via SOS (webhook/SMS/email), start recording
6. Recording stops after 15s of quiet (score < 30)
7. HUD overlay shows FPS, person count, vehicle count, threat level

### Upload Analysis (`web/app.py` → `process_video`)
1. Opens video file, downscales frames
2. Runs same YOLO + violence + gesture pipeline per frame
3. Coalesces events → timeline JSON
4. Writes annotated output video
5. Returns via async API status endpoint

## Dataset

- **Real Life Violence Situations dataset**: `dataset/Real Life Violence Dataset/`
  - `Violence/V_*.mp4` — 1000 violence videos
  - `NonViolence/NV_*.mp4` — 1000+ non-violence videos
- Frame extraction for training: use `dataset/make_videos.py` or OpenCV
- Training was done in Colab with ImageFolder at `Safe5G_Frames/{train,val,test}/{Violence,NonViolence}`

## Git History

- `f7fd3cf` — Initial Colab notebook
- `593f6bf` — Live camera streaming
- `6587f18` — Live dashboard camera streaming
- `40c82f5` — Wired trained violence model + RuleEngine into live pipeline
- `2553d43` — Real cameras page, tests, README accuracy

## Important Notes

- Models (`ai/models/`) are excluded from git — must exist on disk or fail to load
- Database is `safe5g.db` (SQLiteDict-backed) — excluded from git
- Media output directories are tracked but contents excluded
- The gesture detector uses MEDIAPIPE — requires `mediapipe` package
- ReID tracking uses a custom PersonTrackManager in `ai/tracker.py`
- SOS webhook/SMS/email configured via `.env` (`SOS_WEBHOOK`, `SOS_PHONE`, `SOS_EMAIL`)
- `HEADLESS=1` in `.env` disables OpenCV window display
