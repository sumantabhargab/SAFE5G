# Safe5G

**AI-based Women Safety Surveillance System** — Computer Vision + Deep Learning.
The camera becomes the emergency button: a victim who cannot speak or call can
raise an open palm to the nearest camera and the system detects the distress
signal, escalates, and preserves evidence.

Developed at the 5G Use Case Laboratory, Dept. of EEE, IIT Guwahati
(DoT-sponsored summer internship, July 2026).

---

# How it works

```
Camera ──► YOLOv8n (persons / vehicles)
        ├─► Hand Landmarker (open palm = HELP gesture, 5-frame confirmation)
        ├─► EfficientNet-B0 violence classifier (16-frame window voting)
        └─► Rule Engine (threat scoring SAFE→CRITICAL, cooldown-gated alerts)
                │
                ├─► Snapshot + incident record (SQLite)
                ├─► SOS escalation (webhook; SMS/email adapters)
                ├─► Incident recording (video)
                └─► Flask dashboard (live MJPEG feed, real stats from DB)
```

Key detection properties:

- **HELP gesture** works for left and right hands and any reasonable hand
  orientation; requires the palm to hold for 5 consecutive frames, so waving
  or adjusting hair does not trigger it.
- **Violence detection** uses a CNN classifier trained on the Real Life
  Violence Situations dataset (EfficientNet-B0, test F1 0.953); a sliding
  window vote suppresses single-frame false positives.
- **Every alert is real.** The dashboard reads its numbers from the running
  pipeline and the database — there is no simulated data.
- **Alert cooldown** (60 s per type) prevents sustained detections from
  flooding the database and notification channels.

---

# Features

- Real-time CCTV monitoring with MJPEG live feed
- YOLOv8 person/vehicle detection
- Distress (HELP) hand gesture recognition — handedness-aware
- Violence detection with a trained deep-learning model
- Rule-engine threat scoring with levels SAFE / LOW / MEDIUM / HIGH / CRITICAL
- Emergency alert generation with snapshots and cooldown gating
- Incident recording (video) while a threat is active
- Flask dashboard — live feed, real alerts, threat meter, camera status
- SQLite incident database (WAL, thread-safe)
- Report generation (TXT / CSV / JSON)

---

# Folder Structure

```
Safe5G/
├── ai/            # detection pipeline (YOLO, gesture, violence, orchestration)
│   └── models/    # yolov8n.pt, violence_classifier.pth, hand_landmarker.task
├── camera/        # camera manager (capture + MJPEG frame hub)
├── database/      # thread-safe SQLite wrapper
├── media/         # snapshots / recording / report generator
├── rules/         # rule engine (threat scoring), weights.json
├── sensors/       # alert manager, SOS trigger
├── utils/         # config, drawing, helpers
├── web/           # Flask app, templates, dashboard JS/CSS
├── tests/         # core test suite
├── requirements.txt
├── run.py
└── README.md
```

---

# Installation

```bash
git clone https://github.com/sumantabhargab/SAFE5G.git
cd SAFE5G
python -m venv venv
```

Activate (Windows):

```bash
venv\Scripts\activate
```

Activate (Linux/macOS):

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Models

| Model | File | Purpose |
|---|---|---|
| YOLOv8-nano | `ai/models/yolov8n.pt` | person / vehicle detection |
| Violence classifier | `ai/models/violence_classifier.pth` | EfficientNet-B0, trained on Real Life Violence Situations dataset |
| Hand landmarker | `ai/models/hand_landmarker.task` | MediaPipe Tasks, 21 landmarks per hand |

`yolov8n.pt` downloads automatically on first run. `hand_landmarker.task`:

```bash
curl -L -o ai/models/hand_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
```

`violence_classifier.pth` is produced by `notebook1.ipynb` (training notebook).

---

# Run

```bash
python run.py
```

Dashboard: `http://127.0.0.1:5000`

Press `q` in the OpenCV window to quit.

Run the tests:

```bash
python tests/test_core.py
```

---

# Configuration

All thresholds live in `utils/config.py`: camera source and resolution,
YOLO/gesture/violence thresholds, window sizes, alert cooldown, camera
registry (name + location). SOS channels are configured via environment
variables:

```
SOS_WEBHOOK   # HTTPS endpoint that receives alert JSON (with inline snapshot)
SOS_PHONE     # reserved for the SMS adapter
SOS_EMAIL     # reserved for the email adapter
```

---

# Honest status (prototype)

Implemented and working: YOLO detection, HELP gesture detection (with
temporal confirmation), violence classification (window voting), rule-engine
threat scoring, alerting with cooldown, SQLite logging, live dashboard from
real data, report generation.

Prototype limitations (known, by design for v1): single-camera processing
loop; SMS/email adapters are stubs pending credentials; no authentication on
the dashboard; frame-level violence metrics benefit from temporal correlation
between neighbouring frames (video-level generalization is somewhat lower).

---

# Future Scope

5G edge deployment, multi-camera, mobile app, GPS, facial recognition,
audio distress detection, police/ERC integration.

---

# Author

**Sumanta Bhargab** — Safe5G
IEEE CMES Research Project · 5G Use Case Lab, IIT Guwahati
