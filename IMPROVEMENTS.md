# SAFE5G — Improvement Plan & Demo Hardening Checklist

**Date:** 2026-10-11  
**Goal:** Defense/presentation-ready codebase, no fake data, no crashers

---

## Phase 1 — P0 Blockers (Must Fix, ~2 hours)

### Fix 1: Add `threat_level` to DB schema

**File:** `database/database.py:37-47`

Add `threat_level TEXT` to the alerts DDL:

```sql
CREATE TABLE IF NOT EXISTS alerts(
    ...
    image TEXT,
    threat_level TEXT,    -- NEW
    status TEXT,
    created_at TEXT
);
```

Update `db.add_alert()` to accept `threat_level` parameter and include it in the INSERT statement. Update the caller chain: `alert_manager.trigger()` already passes `threat_level` — just wire it through `db.add_alert()`.

**Files changed:** `database/database.py`, `sensors/alert_manager.py`

---

### Fix 2: Remove all hardcoded fake values from HTML templates

**Files:** `web/templates/index.html`, `alerts.html`, `cameras.html`

| Location | Fake Value | Replace With |
|----------|-----------|-------------|
| index.html:245 | `"96.3%" AI Confidence` | `{{ status.threat_score }}%` from `/api/status` |
| index.html:119 | `"99.98% Uptime"` | Remove — no uptime data available |
| index.html:165 | notification badge `5` | `{{ stats.pending }}` from API |
| index.html:159 | `"AR"` / `"Aarti R."` | System admin or remove profile section |
| alerts.html — Detected Objects | Persons=18, Vehicles=9, Bags=5, etc. | Remove panel or wire from `/api/status` |
| alerts.html — Alert Statistics | Today=31, Critical=8, Resolved=17 | Wire from `stats` dict in `/alerts` route |
| cameras.html sidebar | `"8 Cameras Online"` | `{{ status.cameras }} configured / {{ status.online }} online` |
| cameras.html — Quick Actions | Start/Stop buttons (dead links) | Remove or wire to `/api/control` endpoints |

**Files changed:** `web/templates/index.html`, `alerts.html`, `cameras.html`, `web/app.py` (pass extra data to templates)

---

### Fix 3: Wire real module health into `/api/modules`

**File:** `web/app.py:174-186`

Add health tracking to each detector module:

```python
# ai/yolo_detector.py — after __init__ succeeds:
self.ready = True

# ai/gesture_detector.py — after landmarker loads:
self.ready = True

# ai/violence_detector.py — after model loads:
self.ready = True
```

Then in `/api/modules`:

```python
@app.route("/api/modules")
def modules():
    return jsonify({
        "camera": "Running" if camera_manager.get_jpeg() else "Offline",
        "yolo": "Running" if yolo_detector.ready else "Error",
        "gesture": "Running" if gesture_detector.ready else "Error",
        "violence": "Running" if violence_detector.ready else "Error",
        "database": "Connected",
    })
```

**Files changed:** `web/app.py`, `ai/yolo_detector.py`, `ai/gesture_detector.py`, `ai/violence_detector.py`

---

### Fix 4: Remove dead sidebar links

**File:** `web/templates/index.html:83,95`

Remove or comment out:
```html
<!-- <li><a href="history.html">...</a></li> -->
<!-- <li><a href="settings.html">...</a></li> -->
```

Or implement these pages. For a demo, removing is simpler.

**File changed:** `web/templates/index.html`

---

### Fix 5: Fix recording stop condition

**File:** `ai/pipeline.py:176-183`

Replace frame-count-based stop with time-based:

```python
# In __init__:
self.last_trigger_time = 0
self.stop_recording_delay = 15  # seconds

# In process(), replace:
if fired:
    self.last_trigger_time = time.time()
    ...

# Replace the stop condition with:
if self.recording and self.last_trigger_time:
    if time.time() - self.last_trigger_time > self.stop_recording_delay:
        if verdict["score"] < 30:
            media_manager.stop_recording()
            self.recording = False
            self.last_trigger_time = 0
```

**File changed:** `ai/pipeline.py`

---

## Phase 2 — Reliability Fixes (~1.5 hours)

### Fix 6: Camera retry with backoff

**File:** `run.py:47-58`

Replace the hard exit:

```python
import time as time_module

# Replace the consecutive_failures block:
consecutive_failures = 0
retry_delay = 1

while self.running:
    ret, frame = cap.read()
    if not ret or frame is None:
        consecutive_failures += 1
        if consecutive_failures <= 30:
            time_module.sleep(min(retry_delay, 30))
            retry_delay *= 2
        else:
            # After 30 failed reads, keep trying with longer delays
            print("[WARN] Camera stream lost, retrying...")
            time_module.sleep(30)
            continue
        continue
    consecutive_failures = 0
    retry_delay = 1
    ...
```

**File changed:** `run.py`

---

### Fix 7: Headless mode

**File:** `run.py:81`

```python
# Add to config.py:
HEADLESS = os.getenv("SAFE5G_HEADLESS", "0").lower() == "1"

# In run.py start_camera():
if not config.HEADLESS:
    cv2.imshow("Safe5G", result["frame"])
    key = cv2.waitKey(1)
```

**Files changed:** `run.py`, `utils/config.py`

---

### Fix 8: Load `.env` on startup

**File:** `utils/config.py`

Add at the top:

```python
from dotenv import load_dotenv
import os

load_dotenv()
```

Then load SOS variables:

```python
SOS_WEBHOOK = os.getenv("SOS_WEBHOOK", "")
SOS_PHONE = os.getenv("SOS_PHONE", "")
SOS_EMAIL = os.getenv("SOS_EMAIL", "")
```

**File changed:** `utils/config.py`

---

### Fix 9: Create `utils/logger.py`

**New file:** `utils/logger.py`

```python
import logging
import os
from pathlib import Path
from config import LOG_PATH

logger = logging.getLogger("Safe5G")
logger.setLevel(logging.DEBUG)

# File handler
handler = logging.FileHandler(LOG_PATH / "safe5g.log")
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))
logger.addHandler(handler)

# Console handler (optional, for terminal output)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger.addHandler(console)
```

Replace all `print("[ERROR] ...")`, `print("[WARNING] ...")`, `print("[INFO] ...")` across the codebase with `logger.error()`, `logger.warning()`, `logger.info()`.

**Files changed:** `utils/logger.py` (new), `run.py`, `sensors/alert_manager.py`, `sensors/sos_trigger.py`, `utils/helpers.py`

---

## Phase 3 — Code Quality (~1.5 hours)

### Fix 10: Delete dead code

| Dead Code | File | Action |
|-----------|------|--------|
| `GESTURE_MODEL` config | `utils/config.py:17` | Delete line |
| `drawing.py` (unused class) | `utils/drawing.py` | Delete entire file |
| `gunicorn` in requirements | `requirements.txt:18` | Delete line |
| `safe5g.md` in repo root | `safe5g.md` | Delete file (internal analysis) |

---

### Fix 11: Fix `weights.json` consistency

**File:** `rules/weights.json`

Either:
- **Option A (simpler for demo):** Delete all unused keys. Keep only `panic_button` and `alert_cooldown`. Add a comment explaining which engine features use which keys.
- **Option B (full PRD compliance):** Wire `following`, `loitering`, `restricted_zone`, `camera_tampering` into the rule engine with score contributions, matching PRD F4 design.

**Recommendation:** Option A — less risk of breaking the demo.

---

### Fix 12: Fix violence window drift

**File:** `ai/pipeline.py:75-80`

Option A (recommended for demo): classify every frame. Remove the `% 2` skip:

```python
violence = violence_detector.detect(output)
```

If GPU is available, ~20ms/frame is negligible.

Option B: make the window time-based instead of frame-count-based.

---

### Fix 13: Add `.env.example` file

**New file:** `.env.example`

```
# SOS escalation channels
SOS_WEBHOOK=https://your-endpoint.com/alerts
SOS_PHONE=+1234567890
SOS_EMAIL=safety@example.com

# Optional: headless mode for server deployment
SAFE5G_HEADLESS=0

# Optional: override model thresholds
YOLO_CONFIDENCE=0.40
VIOLENCE_THRESHOLD=0.70
GESTURE_THRESHOLD=0.80
```

---

## Phase 4 — Documentation (~30 minutes)

### Fix 14: Update README.md

Changes needed:
1. Clarify that SMS/email adapters are stubs (already stated, but make it more prominent)
2. Add headless mode instructions (`export SAFE5G_HEADLESS=1`)
3. Add `.env.example` reference
4. Remove "single-camera processing loop" from limitations — or keep if you want to be transparent
5. Add known limitations section for honesty
6. Remove the `history.html` / `settings.html` references if those pages are deleted

### Fix 15: Update PRD.md

Changes needed:
1. Mark multi-camera (F15) as "prototype — single camera"
2. Mark evidence capture (F6) as "post-trigger only, no pre-roll buffer"
3. Mark gesture temporal smoothing (F2) as "consecutive frames only, no stability check"
4. Mark SOS email/SMS (F7) as "stub — webhook only"

---

## Phase 5 — Test Improvements (~1 hour)

### Fix 16: Add gesture detector unit test

```python
def test_gesture_open_palm_right():
    """Right hand open palm: all fingertips farther from wrist than PIP joints."""
    lm = [(0,0,0.5), (0.1,0.1,0.5), (0.2,0.05,0.5), ...]  # 21 landmarks
    # Construct landmarks simulating open right hand
    gd = GestureDetector.__new__(GestureDetector)
    gd.FINGER_JOINTS = [(4,3), (8,6), (12,10), (16,14), (20,18)]
    assert gd._open_palm(lm, "Right") == True

def test_gesture_closed_fist():
    """Fist: fingertips closer to wrist than PIP joints."""
    lm = [(0,0,0.5), ...]  # all tips near wrist
    assert gd._open_palm(lm, "Right") == False
```

### Fix 17: Add rule engine scoring test

```python
def test_rule_engine_full_score():
    engine = RuleEngine()
    engine.gesture_frames = 20
    engine.violence_frames = 15
    out = engine.evaluate(
        help_gesture=True,
        violence=True,
        person_count=6,
        gesture_confidence=1.0,
        violence_confidence=0.95,
    )
    assert out["score"] > 75  # Should trigger with SOS + violence + crowd
    assert out["level"] in ("HIGH", "CRITICAL")
    assert "SOS Gesture" in out["reasons"]
    assert "Violence" in out["reasons"]
    assert "Crowd" in out["reasons"]
```

### Fix 18: Make smoke test skip if models missing

```python
def test_pipeline_process_smoke():
    import numpy as np
    from ai.pipeline import pipeline
    
    # Check models exist before running
    from pathlib import Path
    from utils.config import YOLO_MODEL, VIOLENCE_MODEL, GESTURE_MODEL
    model_dir = YOLO_MODEL.parent
    missing = [m for m in [YOLO_MODEL, VIOLENCE_MODEL, model_dir/"hand_landmarker.task"]
               if not m.exists()]
    if missing:
        pytest.skip(f"Missing models: {[m.name for m in missing]}")
    
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    result = pipeline.process(frame)
    assert "frame" in result
```

---

## Execution Order (Recommended)

```
Phase 1 (blockers)  →  Fix 1-5
Phase 2 (reliability) →  Fix 6-9
Phase 3 (quality)     →  Fix 10-13
Phase 4 (docs)        →  Fix 14-15
Phase 5 (tests)       →  Fix 16-18
```

**Total estimated effort:** ~5 hours for a confident demo.

**Critical path:** Phase 1 only. These 5 fixes eliminate all showstopper bugs that an examiner would notice.

---

## File Change Summary

| File | Status | Changes |
|------|--------|---------|
| `database/database.py` | **Modify** | Add threat_level column + param |
| `sensors/alert_manager.py` | **Modify** | Pass threat_level through |
| `web/app.py` | **Modify** | Real module health, extra template data |
| `web/templates/index.html` | **Modify** | Remove fake values, dead links |
| `web/templates/alerts.html` | **Modify** | Remove fake numbers |
| `web/templates/cameras.html` | **Modify** | Remove fake numbers |
| `ai/pipeline.py` | **Modify** | Fix recording stop, fix violence skip |
| `ai/yolo_detector.py` | **Modify** | Add `self.ready` flag |
| `ai/gesture_detector.py` | **Modify** | Add `self.ready` flag |
| `ai/violence_detector.py` | **Modify** | Add `self.ready` flag |
| `run.py` | **Modify** | Camera retry, headless mode, signal handling |
| `utils/config.py` | **Modify** | Remove GESTURE_MODEL, add .env load, HEADLESS |
| `utils/logger.py` | **Create** | New logging module |
| `utils/drawing.py` | **Delete** | Dead code |
| `.env.example` | **Create** | New env template |
| `requirements.txt` | **Modify** | Remove gunicorn |
| `safe5g.md` | **Delete** | Internal analysis, not for repo |
| `tests/test_core.py` | **Modify** | Add gesture test, rule test, smoke fix |
| `rules/weights.json` | **Modify** | Remove unused keys |
| `README.md` | **Modify** | Update limitations, add env instructions |
| `PRD.md` | **Modify** | Mark unimplemented features |

**22 files: 15 modify, 2 create, 2 delete, 1 update (requirements), 2 doc updates**
