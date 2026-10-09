# SAFE5G — Product Requirements Document (PRD)

**Version:** 1.0 · **Date:** 2026-10-09 · **Owner:** Sumanta Bhargab
**Product:** Safe5G — Multi-Modal AI Surveillance for Real-Time Threat Detection & Emergency Notification

---

## 1. Vision

SAFE5G turns passive CCTV into an active safety guardian for women in public spaces.
A person in danger — unable to shout, run, or call — can raise an open palm to the nearest
camera, and within seconds the system detects the distress signal, escalates to responders,
and preserves evidence. No button, no app, no phone required: the camera is the SOS button.

**One-line pitch:** *The camera becomes the emergency button.*

## 2. Problem

- Existing CCTV is forensic, not preventive — footage is reviewed after harm is done.
- Victims in assault situations often cannot speak, dial, or move; voice/text-based SOS
  channels fail exactly when they're needed most.
- One guard cannot watch dozens of feeds; attention lapses are measured in minutes.
- Emergency response time is the single biggest determinant of outcome in violent incidents.

## 3. Target users & scenarios

| User | Need |
|---|---|
| Public-space security operator (campus, transit, mall) | See threats live, get prioritized alerts, verify with video evidence |
| Emergency responder / police | Receive incident alert with location, snapshot, camera ID |
| Institution admin (college, hospital, workplace) | Incident log, reports, audit trail, deterrence |
| Woman in distress | Silent, hands-visible way to summon help without a phone |

Primary demo scenario: a woman near a campus ATM/gate raises her palm to the camera;
system detects HELP gesture → escalates → dashboard shows incident + snapshot within seconds.

## 4. Product principles

1. **Every alert is real** — no simulated data anywhere in the product. A simulated/demo
   mode must be explicitly labeled, never mixed with live data.
2. **Detection must be defensible** — models are trained on real datasets with published
   metrics; operators see confidence scores, not just binaries.
3. **Fail loud, not silent** — camera loss, model load failure, DB errors are surfaced,
   not swallowed.
4. **Privacy by design** — snapshots and logs stored locally; no cloud upload by default;
   clear retention policy (auto-purge configurable).
5. **Prototype ≠ production claim** — documentation states exactly what is and isn't
   validated.

## 5. Functional requirements

### 5.1 Detection engine (P0)
- **F1 — Person/vehicle detection:** YOLOv8n on live frames; persons tracked with
  confidence ≥ 0.40; per-frame counts exposed to the app.
- **F2 — Distress gesture recognition:** open-palm HELP gesture via hand-landmark model.
  - Must work for left AND right hands, any reasonable hand orientation.
  - Requires temporal confirmation: N consecutive frames (default 5) to trigger —
    eliminates single-frame false positives (waving, adjusting hair).
  - Per-hand confidence reported.
- **F3 — Violence detection:** trained CNN classifier (EfficientNet-B0,
  `violence_classifier.pth`, test F1 0.953) evaluated over a sliding window of frames
  (default: 16-frame window, positive if ≥ 8 frames classified violent, i.e. ~50% vote).
  - Replaces all motion-heuristic detection.
  - Alerts include model confidence (0–1) and window evidence.
- **F4 — Threat scoring:** RuleEngine is the single authority for threat level
  (SAFE/LOW/MEDIUM/HIGH/CRITICAL):
  - Weighted fusion of gesture, violence, crowd density, loitering, restricted-zone events.
  - All confidence inputs normalized to 0–100 before scoring.
  - Temporal debounce and EMA smoothing as already designed in `rules/rule_engine.py`.
  - Rule weights loaded from `rules/weights.json` (single source of truth).

### 5.2 Alerting & escalation (P0)
- **F5 — Alert generation:** one alert per event, gated by cooldown (default 60 s per
  type per camera). Alert contains: type, camera, location, timestamp (full date + time,
  timezone-aware), confidence, snapshot image path, threat level.
- **F6 — Evidence capture:** snapshot at trigger moment; optional pre/post video clip
  (default 10 s around event) saved to `media/`.
- **F7 — SOS escalation:** pluggable channels — webhook (real, with HTTP status checking
  + 1 retry), SMS and email adapters behind a common interface (Twilio/SMTP
  implementations stubbed but clearly marked "not configured" in UI until credentials set).
  - Escalation attaches the snapshot.
  - Per-event escalation, not per-frame: gated by the same cooldown.

### 5.3 Dashboard & monitoring (P0)
- **F8 — Live feed:** MJPEG stream, throttled to ≤ 15 fps, graceful "camera offline"
  placeholder when no frames; supports multiple concurrent viewers without extra CPU load
  (single shared frame buffer).
- **F9 — Real dashboard data:** all stats (alert counts, pending/resolved, threat level,
  module status, FPS, people count) read from the actual system state + DB. **No hardcoded
  values.**
- **F10 — Alerts page:** rendered from `recent_alerts()`; resolve/delete actions persist to
  DB; filter by type/status/date.
- **F11 — Live threat overlay on video:** bounding boxes colored by threat level, gesture
  and violence indicators, camera/location banner, non-duplicated FPS.

### 5.4 Data & reporting (P1)
- **F12 — Incident database:** SQLite, WAL mode, single writer with lock, absolute DB
  path; schema: alerts(id, type, camera, location, timestamp, confidence, threat_level,
  status, snapshot_path, resolved_at) + logs table.
- **F13 — Reports:** TXT/CSV/JSON export of alert history with summary stats (exists;
  harden with error handling).

### 5.5 Configuration & ops (P1)
- **F14 — Config file:** cameras (id, name, location, source URL/index), thresholds,
  cooldowns, contact endpoints (webhook URL, SMS/email creds via .env) — all externalized;
  no hardcoded camera metadata in code.
- **F15 — Multi-camera:** ≥ 2 concurrent camera sources processed round-robin or
  thread-per-camera; per-camera pipeline state (violence window, cooldowns).
- **F16 — Graceful failure:** camera disconnect → retry with backoff, dashboard shows
  offline; model file missing → clear startup error naming the file; headless mode
  (no cv2.imshow) for server deployment.
- **F17 — Cross-platform:** no Windows-only imports at module level (winsound lazy-loaded,
  optional).

## 6. Non-functional requirements

| NFR | Requirement |
|---|---|
| Performance | ≥ 10 FPS end-to-end on a laptop GPU (detection + classification + overlay); ≤ 2 s from detection to dashboard alert |
| Reliability | 8 h continuous run without memory growth (tracker prune, no unbounded lists) |
| Security | Flask debug OFF; bind 127.0.0.1 by default; no auth in prototype but a documented path to add it; no secrets in repo (Kaggle key revoked & scrubbed from git history) |
| Reproducibility | `pip install -r requirements.txt` works on Python 3.10–3.12; no BOM; models fetched by documented script, not committed binaries |
| Code quality | No dead modules (delete or wire); no bare `import config`; single config module; no print-debugging (use `utils/logger.py`) |
| Testability | Unit tests for RuleEngine scoring, gesture logic (synthetic landmarks), DB layer; smoke test that pipeline processes one synthetic frame end-to-end |

## 7. Out of scope (v1)

- 5G network integration (documented as future scope / research context)
- Mobile app, GPS, cloud deployment
- Facial recognition, audio detection
- Real-time tracking of persons across cameras
- User accounts / multi-tenant dashboard

## 8. Success metrics

| Metric | Target |
|---|---|
| Gesture trigger precision in demo conditions (palm held 2 s) | ≥ 95% trigger, 0 false triggers from waving in a 5-min demo |
| Violence classifier | Test F1 ≥ 0.90 (achieved: 0.953), live-window behavior qualitatively correct |
| Dashboard integrity | 100% of displayed numbers traceable to DB/system state |
| Alert latency | Detection → dashboard alert < 2 s |
| False alert rate | ≤ 1 alert/min sustained under normal walk-through activity |

## 9. Milestones

| Phase | Deliverable |
|---|---|
| M1 — Stabilize | Fix crashers (colors, imports, paths), debug off, MJPEG throttle, SQLite locking |
| M2 — Real intelligence | violence_classifier wired with window voting; RuleEngine wired with scale fix + weights.json; cooldowns |
| M3 — Real dashboard | /api endpoints + alerts page from DB; no frontend simulation; resolve/delete persist |
| M4 — Demo hardening | gesture handedness + temporal smoothing; multi-camera config; graceful failure; demo script |
| M5 — Presentation | README accuracy pass, architecture diagram, demo rehearsal, report claim alignment |

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Violence model false-positives on live webcam (train/test domain gap) | Window voting + confidence display + threshold tunable in config; demo script uses clear scenarios |
| Gesture FP (any open palm) | Temporal confirmation (N frames) + palm-stillness check |
| examiner probes "is this real?" | Everything on screen sourced from DB/pipeline; demo mode explicitly labeled |
| Weak hardware at presentation | YOLOv8n (nano), frame skip option, pre-rendered backup video of demo |
| Leaked Kaggle key discovered | Revoke now; scrub history; document rotation |

## 11. Open questions

1. Presentation date? (drives M1–M5 scheduling)
2. Will the demo run on your laptop webcam, lab CCTV, or recorded video? (determines
   multi-camera priority)
3. Should SMS/email stay stubbed-but-labeled, or is a real Twilio account available for
   the demo?
4. Is there an institutional API/endpoint (campus security) the webhook could target in
   the demo, or do we demo the webhook with a local receiver?
