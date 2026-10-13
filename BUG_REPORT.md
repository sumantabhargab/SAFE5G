# SAFE5G — Comprehensive Bug Report

**Date:** 2026-10-11  
**Scope:** All modules under `SAFE5G/`  
**Severity scale:** P0 (crash/demo-breaker) → P3 (nice-to-fix)

---

## P0 — Critical Bugs (Must Fix Before Any Demo)

### B0-1: DB schema missing `threat_level` column

**File:** `database/database.py:37-47` (alerts table DDL)  
**Impact:** `alert_manager.trigger()` accepts a `threat_level` parameter, which `sos_trigger.help_detected()` and `sos_trigger.violence_detected()` pass through. The `alerts.html` template references `a.threat_level`. But the `alerts` table has no `threat_level TEXT` column — the column simply doesn't exist in the CREATE TABLE DDL.

**Failure scenario:** When an alert is created, `db.add_alert()` ignores the `threat_level` column because it's not in the INSERT statement. The alert_manager returns `threat_level` in the alert dict, but `db.recent_alerts()` never includes it. The `/alerts` page shows `"Violence"` as critical only by guessing from `alert_type`, not from actual threat data.

**Fix:** Add `threat_level TEXT` to the alerts table DDL. Pass `threat_level` through `db.add_alert()`.

---

### B0-2: Hardcoded fake values in HTML templates

**Files & lines:**
- `web/templates/index.html:245` — `"96.3%" AI Confidence` (static, never from API)
- `web/templates/index.html:119` — `"99.98% Uptime"` in sidebar footer
- `web/templates/index.html:165` — notification badge hardcoded to `5`
- `web/templates/index.html:159` — profile avatar `"AR"` / `"Aarti R."` (static)
- `web/templates/alerts.html` — hard-coded numbers in "Detected Objects" panel: Persons=18, Vehicles=9, Bags=5, etc.
- `web/templates/alerts.html` — "Alert Statistics" panel: Today=31, Critical=8, Resolved=17
- `web/templates/cameras.html` — sidebar says `"8 Cameras Online"` (hardcoded)

**Impact:** PRD F9 requires "100% of displayed numbers traceable to DB/system state." These values are demonstrably fake and will be caught by examiners.

**Fix:** Wire `/api/status` data into these template elements. Remove all static numbers.

---

### B0-3: `/api/modules` returns hardcoded "Running" for all AI modules

**File:** `web/app.py:174-186`  
**Impact:** The endpoint always returns `{"yolo": "Running", "gesture": "Running", "violence": "Running", "database": "Connected"}` regardless of whether the models actually loaded. If the violence model crashes on load, the dashboard still reports it healthy. Violates PRD F9.

**Fix:** Track health status on each detector (e.g., `yolo_detector.ready = True/False`). Read those flags in `/api/modules`.

---

### B0-4: Missing dead links in sidebar navigation

**File:** `web/templates/index.html:83,95`  
**Impact:** Sidebar contains links to `history.html` and `settings.html` which do not exist. Clicking them returns Flask 404.

**Fix:** Either create these pages or remove the links.

---

### B0-5: Recording stop condition can never trigger

**File:** `ai/pipeline.py:176-183`  
**Code:**
```python
if verdict["score"] < 30 and self.frames_since_alert > 5 * 30:
```
**Impact:** `frames_since_alert` only resets when an alert fires. If the threat score fluctuates between 29 and 31, recording never stops because the condition requires BOTH score < 30 AND > 150 frames of quiet. A score that oscillates at 30 traps recording indefinitely — video files grow unbounded.

**Fix:** Use `time.time()` delta instead of frame count. Track `self.last_trigger_time`. Stop when `now - self.last_trigger_time > 30` seconds AND score < 30.

---

## P1 — Correctness Bugs

### B1-1: `weights.json` is a documentation mismatch — 9 of 12 keys unused

**File:** `rules/weights.json:1-12` vs `rules/rule_engine.py:13-21`  
**Impact:** PRD F4 says "Rule weights loaded from weights.json (single source of truth)." Only 3 keys (`alert_cooldown`, `panic_button`, `running`) are loaded. The file contains `following`, `loitering`, `restricted_zone`, `shake_sensor`, `night_time`, `crowd`, `rapid_direction_change`, `camera_tampering` — all never referenced by the rule engine. This is misleading.

**Fix options:**
1. Delete unused keys and document only what's loaded.
2. Wire all keys into the rule engine and remove unused default fallbacks.
3. Mark the file as "planned weights, partial implementation" in PRD.

---

### B1-2: `GESTURE_MODEL` in config.py points to non-existent file

**File:** `utils/config.py:17`  
**Code:** `GESTURE_MODEL = MODEL_DIR / "gesture.onnx"`  
**Impact:** No code in the project loads `.onnx` files. The gesture detector uses MediaPipe's `.task` format (`gesture_detector.py:45`). This is dead config. If someone reads it, they'll try to load a non-existent file.

**Fix:** Remove `GESTURE_MODEL` from config.py.

---

### B1-3: Two separate cooldown mechanisms, neither documented

**Files:** `rules/rule_engine.py:207-212` AND `sensors/alert_manager.py:41-51`  
**Impact:** The rule engine enforces its own cooldown (from `weights.json["cooldown_seconds"]`, default 10s). The alert manager enforces a separate cooldown (from `ALERT_COOLDOWN` in config, default 60s). Both gate the same alert — an alert must pass BOTH cooldowns. This doubles the effective cooldown but is never documented. If someone tunes one, the other silently overrides.

**Fix:** Remove the redundant cooldown. Use one authoritative source.

---

### B1-4: Violence detector window drifts when frame skipping

**File:** `ai/pipeline.py:75-80`  
**Code:**
```python
if self.frame_counter % 2 == 0 or self.last_violence is None:
    violence = violence_detector.detect(output)
```
**Impact:** When classified every 2nd frame, the violence detector's internal `self.window` list receives entries only half as fast. A 16-frame window at 30fps should fill in ~0.53s, but with skip it fills in ~1.06s. The `VIOLENCE_WINDOW_VOTES=8` (50% vote) threshold becomes unreliable because the window is twice as long in wall-clock time.

**Fix:** Either classify every frame (EfficientNet-B0 on GPU is ~20ms/frame) or decouple the window size from frame count (use a time-based sliding window).

---

### B1-5: `threat_level` passed to `alert_manager.trigger()` but not stored in DB

**File:** `sensors/alert_manager.py:69,100`  
**Impact:** `trigger()` accepts `threat_level=None` and puts it in the returned alert dict, but `db.add_alert()` has no `threat_level` parameter (B0-1). The alert dict has the field but the DB row doesn't — data loss.

**Fix:** Same fix as B0-1 — add column, pass through.

---

### B1-6: `drawing.py` is dead code — never called

**File:** `utils/drawing.py`  
**Impact:** `Drawer.draw_person()`, `Drawer.draw_statistics()`, `Drawer.draw_zone()`, `Drawer.draw_line()` are defined but never imported or called by any module. The pipeline does its own HUD overlay directly in `ai/pipeline.py`.

**Fix:** Either wire it in or delete it.

---

## P2 — Reliability Bugs

### B2-1: No camera retry/backoff — hard exit on stream loss

**File:** `run.py:47-58`  
**Code:** `consecutive_failures > 30` → exit with `"Camera stream lost. Exiting."`  
**Impact:** If the webcam disconnects for any reason (USB, driver, laptop lid), the entire application exits. PRD F16 requires "camera disconnect → retry with backoff, dashboard shows offline."

**Fix:** Replace hard exit with exponential backoff (1s → 2s → 4s → max 30s). Dashboard shows offline via `/api/status` returning `cameras: 0`.

---

### B2-2: No model-load error handling — crash at import time

**Files:** `ai/yolo_detector.py:35-39`, `ai/gesture_detector.py:44-63`, `ai/violence_detector.py:36-72`  
**Impact:** Module-level singleton instantiation means all three models load at import time (before `run.py` even reaches `__main__`). If any model is missing, the program crashes with an opaque traceback. No graceful fallback or clear error message.

**Fix:** Add startup checks in `run.py` that test for model existence and print clear messages before starting the pipeline.

---

### B2-3: `cv2.imshow()` crashes headless deployments

**File:** `run.py:81`  
**Code:** `cv2.imshow("Safe5G", result["frame"])`  
**Impact:** On any system without a display server (Linux headless, CI, Docker), this crashes the entire process. PRD F16 requires "headless mode (no cv2.imshow)."

**Fix:** Add a `HEADLESS` config flag. Skip `cv2.imshow` when True.

---

### B2-4: Flask daemon thread killed without shutdown hooks

**File:** `run.py:101-108`  
**Impact:** Dashboard runs as daemon thread. Main thread blocks on `start_camera()`. Ctrl-C kills the daemon without Flask shutdown hooks, potentially leaving processes in bad state.

**Fix:** Use `signal` module to handle SIGINT gracefully, or use `flask run` in a subprocess.

---

### B2-5: python-dotenv installed but never used

**File:** `requirements.txt:17` (`python-dotenv`)  
**Impact:** `.env` files have no effect. `sos_trigger.py` reads `os.getenv("SOS_WEBHOOK")` etc., but there's no `load_dotenv()` call. A user who creates a `.env` file finds nothing changes.

**Fix:** Add `from dotenv import load_dotenv; load_dotenv()` to `utils/config.py`.

---

## P3 — Quality & Maintainability

### B3-1: All `print()` calls, no logging system

**Impact:** 18 bare `print()` calls across the codebase. PRD says "no print-debugging (use utils/logger.py)" but `utils/logger.py` does not exist.

**Fix:** Create `utils/logger.py` using Python's `logging` module with file handler pointing to `LOG_PATH`.

---

### B3-2: No type hints anywhere

**Impact:** Zero type annotations across 16 Python files. Makes code harder to review, refactor, or extend.

---

### B3-3: Global singletons everywhere

**Impact:** Every module has a module-level singleton (`yolo_detector`, `gesture_detector`, `violence_detector`, `rule_engine`, `alert_manager`, `sos_trigger`, `media_manager`, `camera_manager`, `db`, `app`, `pipeline`). Makes testing difficult, prevents multiple instances, creates circular-import risk.

---

### B3-4: Triple `frame.copy()` per pipeline frame

**File:** `ai/pipeline.py`  
**Impact:** Each detector copies the frame: YOLO (line 40), violence (line 66), gesture (line 77). Three full memory copies per frame = ~25-30% CPU overhead.

**Fix:** Pipeline owns one mutable frame buffer; each detector annotates in-place.

---

## Test Gaps

| Area | Test Exists? | Status |
|------|-------------|--------|
| RuleEngine score calculation | Partial (`test_rule_engine_scale_normalization`) | Trivially asserts score >= 0 |
| RuleEngine EMA smoothing | No | Missing |
| RuleEngine vehicle/crowd scoring | No | Missing |
| AlertManager `_should_fire` cooldown | No | Missing |
| AlertManager `notify` callback | No | Missing |
| GestureDetector `_open_palm` logic | No | **Major gap** — core safety feature |
| ViolenceDetector model loading | No | Missing |
| ViolenceDetector window voting (full) | Partial (mocked) | Skips real model path |
| SOSTrigger webhook retry | No | Missing |
| ReportGenerator export | No | Missing |
| MediaManager recording cycle | No | Missing |
| DB error paths (invalid path, concurrent writes) | No | Missing |
| Pipeline end-to-end with mocks | Yes (`test_pipeline_process_smoke`) | Requires all 3 model files — fails in CI |

---

## Summary Matrix

| Category | Count | P0 | P1 | P2 | P3 |
|----------|-------|----|----|----|----|
| Bugs      | 21    | 5  | 6  | 5  | 5  |
| Test gaps | 12    | —  | —  | —  | —  |
| PRD mismatches | 4 | —  | 4  | —  | —  |

**Total blocking issues for demo:** 5 (B0-1 through B0-5)
