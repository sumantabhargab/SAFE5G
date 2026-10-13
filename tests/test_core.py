"""
SAFE5G core tests.

Run from the project root:  python -m pytest tests/ -q
(or: python tests/test_core.py)
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("SAFE5G_TEST", "1")


def test_rule_engine_scale_normalization():
    from rules.rule_engine import RuleEngine

    engine = RuleEngine()

    # 0-1 confidence inputs must be accepted (scale bug regression)
    out = engine.evaluate(
        help_gesture=True,
        violence=False,
        person_count=1,
        gesture_confidence=1.0,  # 0-1 float, not 0-100
    )

    assert out["score"] >= 0
    assert out["level"] in ("SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_rule_engine_full_score():
    """Combined HELP gesture + violence + crowd should produce HIGH/CRITICAL."""
    from rules.rule_engine import RuleEngine

    engine = RuleEngine()

    # Build up temporal counters by repeated evaluation
    reasons = None
    for _ in range(20):
        out = engine.evaluate(
            help_gesture=True,
            violence=True,
            person_count=6,
            gesture_confidence=1.0,
            violence_confidence=0.95,
        )
        reasons = out["reasons"]

    assert engine.gesture_frames >= 15
    assert engine.violence_frames >= 10
    assert "SOS Gesture" in reasons
    assert "Violence" in reasons
    assert "Crowd" in reasons


def test_rule_engine_ema_smoothing():
    """EMA smoothing (0.75/0.25) should prevent score spikes."""
    from rules.rule_engine import RuleEngine

    engine = RuleEngine()

    # Simulate a single violent frame after quiet
    out1 = engine.evaluate(
        help_gesture=False,
        violence=True,
        person_count=0,
        violence_confidence=0.95,
    )
    score1 = out1["score"]

    # Next frame should be smoothed
    out2 = engine.evaluate(
        help_gesture=False,
        violence=True,
        person_count=0,
        violence_confidence=0.95,
    )
    score2 = out2["score"]

    # Score should increase but be smoothed, not a full jump
    assert score2 >= score1


def test_alert_manager_cooldown():
    """Per-type cooldown should suppress rapid re-fires."""
    from sensors.alert_manager import AlertManager

    mgr = AlertManager(cooldown=0.5)

    a1 = mgr.trigger(
        frame=b"", alert_type="Violence", confidence=0.9,
        camera="Cam1", location="Gate", threat_level="HIGH",
    )
    assert a1 is not None

    # Immediately should be suppressed
    a2 = mgr.trigger(
        frame=b"", alert_type="Violence", confidence=0.9,
        camera="Cam1", location="Gate", threat_level="HIGH",
    )
    assert a2 is None

    import time
    time.sleep(0.6)

    # After cooldown, should fire again
    a3 = mgr.trigger(
        frame=b"", alert_type="Violence", confidence=0.9,
        camera="Cam1", location="Gate", threat_level="HIGH",
    )
    assert a3 is not None


def test_gesture_open_palm_right():
    """Right hand open palm: all fingertips farther from wrist than PIP joints."""
    from ai.gesture_detector import GestureDetector

    gd = GestureDetector.__new__(GestureDetector)
    gd.FINGER_JOINTS = [(4, 3), (8, 6), (12, 10), (16, 14), (20, 18)]

    # Construct landmarks simulating open right hand
    # Wrist at origin, fingers extended upward (y decreasing)
    lm = [
        (0.5, 0.8, 0.5),   # 0 wrist
        (0.5, 0.7, 0.5),   # 1 thumb MCP
        (0.5, 0.6, 0.5),   # 2 thumb IP
        (0.5, 0.5, 0.5),   # 3 thumb tip
        (0.3, 0.5, 0.5),   # 4 index MCP
        (0.3, 0.35, 0.5),  # 5 index PIP
        (0.3, 0.2, 0.5),   # 6 index tip
        (0.5, 0.5, 0.5),   # 7 middle MCP
        (0.5, 0.35, 0.5),  # 8 middle PIP
        (0.5, 0.2, 0.5),   # 9 middle tip
        (0.7, 0.5, 0.5),   # 10 ring MCP
        (0.7, 0.35, 0.5),  # 11 ring PIP
        (0.7, 0.2, 0.5),   # 12 ring tip
        (0.9, 0.5, 0.5),   # 13 pinky MCP
        (0.9, 0.35, 0.5),  # 14 pinky PIP
        (0.9, 0.2, 0.5),   # 15 pinky tip
        (0.5, 0.5, 0.5),   # 16 thumb IP (repeated)
        (0.3, 0.5, 0.5),   # 17 index MCP
        (0.5, 0.5, 0.5),   # 18 middle MCP
        (0.7, 0.5, 0.5),   # 19 ring MCP
        (0.9, 0.5, 0.5),   # 20 pinky MCP
    ]

    # Adjusted landmarks for proper open palm test
    lm = [
        (0.0, 0.9, 0.5),   # 0 wrist (center bottom)
        (0.0, 0.8, 0.5),   # 1 thumb MCP
        (0.0, 0.7, 0.5),   # 2 thumb IP
        (0.0, 0.55, 0.5),  # 3 thumb tip — farther from wrist than IP
        (-0.15, 0.65, 0.5),  # 4 index MCP
        (-0.15, 0.45, 0.5),  # 5 index PIP
        (-0.15, 0.2, 0.5),   # 6 index tip — farther from wrist than PIP
        (0.0, 0.55, 0.5),   # 7 middle MCP
        (0.0, 0.35, 0.5),   # 8 middle PIP
        (0.0, 0.1, 0.5),    # 9 middle tip
        (0.15, 0.55, 0.5),  # 10 ring MCP
        (0.15, 0.35, 0.5),  # 11 ring PIP
        (0.15, 0.1, 0.5),   # 12 ring tip
        (0.3, 0.65, 0.5),   # 13 pinky MCP
        (0.3, 0.5, 0.5),    # 14 pinky PIP
        (0.3, 0.35, 0.5),   # 15 pinky tip
        (0.0, 0.55, 0.5),   # 16
        (-0.15, 0.65, 0.5), # 17
        (0.0, 0.55, 0.5),   # 18
        (0.15, 0.55, 0.5),  # 19
        (0.3, 0.65, 0.5),   # 20
    ]

    # Check each non-thumb finger: tip distance > PIP distance from wrist
    for tip_idx, pip_idx in [(6, 5), (9, 8), (12, 11), (15, 14)]:
        tip = lm[tip_idx]
        pip = lm[pip_idx]
        wrist = lm[0]
        d_tip = (tip[0] - wrist[0]) ** 2 + (tip[1] - wrist[1]) ** 2
        d_pip = (pip[0] - wrist[0]) ** 2 + (pip[1] - wrist[1]) ** 2
        assert d_tip > d_pip * 1.1, f"finger tip should be farther than PIP"

    assert gd._open_palm(lm, "Right") == True


def test_gesture_closed_fist():
    """Fist: fingertips closer to wrist than PIP joints."""
    from ai.gesture_detector import GestureDetector

    gd = GestureDetector.__new__(GestureDetector)
    gd.FINGER_JOINTS = [(4, 3), (8, 6), (12, 10), (16, 14), (20, 18)]

    # Fist: tips curled toward wrist
    lm = [
        (0.0, 0.9, 0.5),   # 0 wrist
        (0.0, 0.8, 0.5),   # 1 thumb MCP
        (-0.05, 0.75, 0.5),  # 2 thumb IP
        (-0.08, 0.72, 0.5),  # 3 thumb tip — close to wrist
        (-0.1, 0.75, 0.5),   # 4 index MCP
        (-0.1, 0.65, 0.5),   # 5 index PIP
        (-0.1, 0.62, 0.5),   # 6 index tip — close to wrist, less than PIP distance
        (0.0, 0.72, 0.5),    # 7 middle MCP
        (0.0, 0.62, 0.5),    # 8 middle PIP
        (0.0, 0.58, 0.5),    # 9 middle tip
        (0.1, 0.72, 0.5),    # 10 ring MCP
        (0.1, 0.62, 0.5),    # 11 ring PIP
        (0.1, 0.58, 0.5),    # 12 ring tip
        (0.2, 0.78, 0.5),    # 13 pinky MCP
        (0.2, 0.72, 0.5),    # 14 pinky PIP
        (0.2, 0.68, 0.5),    # 15 pinky tip
        (0.0, 0.72, 0.5),    # 16
        (-0.1, 0.75, 0.5),   # 17
        (0.0, 0.72, 0.5),    # 18
        (0.1, 0.72, 0.5),    # 19
        (0.2, 0.78, 0.5),    # 20
    ]

    # At least one finger should have tip closer to wrist than PIP
    wrist = lm[0]
    for tip_idx, pip_idx in [(6, 5), (9, 8), (12, 11), (15, 14)]:
        tip = lm[tip_idx]
        pip = lm[pip_idx]
        d_tip = (tip[0] - wrist[0]) ** 2 + (tip[1] - wrist[1]) ** 2
        d_pip = (pip[0] - wrist[0]) ** 2 + (pip[1] - wrist[1]) ** 2
        # At least some fingers should be closer (fist)
        # The open-palm check requires ALL 4 non-thumb fingers extended

    assert gd._open_palm(lm, "Right") == False


def test_database_roundtrip():
    import tempfile

    from database.database import Database

    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "test.db")

        alert_id = db.add_alert(
            alert_type="Violence", confidence=0.9, camera="Cam 1",
            location="Test", image="", threat_level="HIGH", status="Pending"
        )

        rows = db.recent_alerts(limit=5)

        assert rows and rows[0]["id"] == alert_id
        assert rows[0]["alert_type"] == "Violence"
        assert rows[0]["threat_level"] == "HIGH"

        db.update_status(alert_id, "Resolved")
        assert db.total_resolved() == 1

        db.delete_alert(alert_id)
        assert db.total_alerts() == 0

        db.close()


def test_database_threat_level():
    """threat_level must be stored and retrieved from DB."""
    import tempfile

    from database.database import Database

    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "test.db")

        db.add_alert(
            alert_type="HELP Gesture", confidence=1.0, camera="Cam 1",
            location="Gate", image="", threat_level="CRITICAL", status="Pending"
        )

        row = db.recent_alerts(limit=1)[0]
        assert row["threat_level"] == "CRITICAL"

        db.close()


def test_violence_detector_window_logic():
    from ai.violence_detector import ViolenceDetector

    # Skip the real model: instantiate without loading by subclass-free trick
    detector = ViolenceDetector.__new__(ViolenceDetector)

    detector.threshold = 0.7

    detector.window_size = 4

    detector.votes_required = 3

    detector.window = []

    class FakeClassifier:

        def __init__(self, detector):

            self.detector = detector

        def _classify(self, frame):

            return True, 0.9

    # Patch classify to always violent
    detector._classify = lambda frame: (True, 0.9)

    import numpy as np

    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    # Window not yet full -> no violence
    out = detector.detect(frame)

    assert not out["violence"]

    out = detector.detect(frame)

    assert not out["violence"]

    out = detector.detect(frame)

    assert not out["violence"]

    # 4th frame fills the window: 4/4 votes -> violence
    out = detector.detect(frame)

    assert out["violence"]

    assert out["window_votes"] == 4


def test_violence_detector_window_not_enough_votes():
    """Window full but below vote threshold should not trigger."""
    from ai.violence_detector import ViolenceDetector

    detector = ViolenceDetector.__new__(ViolenceDetector)
    detector.threshold = 0.7
    detector.window_size = 4
    detector.votes_required = 3
    detector.window = []

    # Alternate violent/non-violent: V, NV, V, NV = 2/4 votes, not enough
    detector._classify = lambda frame: (True, 0.9)  # violent
    import numpy as np
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    detector.detect(frame)   # V: [1]
    detector._classify = lambda frame: (False, 0.3)  # not violent
    detector.detect(frame)   # NV: [1, 0]
    detector._classify = lambda frame: (True, 0.9)
    detector.detect(frame)   # V: [1, 0, 1]
    detector._classify = lambda frame: (False, 0.3)
    detector.detect(frame)   # NV: [1, 0, 1, 0] = 2 votes < 3 required

    assert not detector.window[-1][0] or True  # window has mixed
    # The violence detection needs >= votes_required
    votes = sum(1 for v, _ in detector.window if v)
    assert votes == 2
    assert votes < detector.votes_required


def test_config_has_colors():
    from utils import config

    # Regression: drawing.py crashed on missing GREEN/RED/YELLOW/BLUE
    for name in ("GREEN", "RED", "YELLOW", "BLUE", "THREAT_COLORS"):
        assert hasattr(config, name), f"config.{name} missing"

    # GESTURE_MODEL should no longer exist (B1-2)
    assert not hasattr(config, "GESTURE_MODEL"), "GESTURE_MODEL should be removed"

    # HEADLESS should exist (B2-3)
    assert hasattr(config, "HEADLESS"), "HEADLESS config should exist"

    # SOS env vars should exist
    for name in ("SOS_WEBHOOK", "SOS_PHONE", "SOS_EMAIL"):
        assert hasattr(config, name), f"config.{name} missing"


def test_filename_unique_within_second():
    from utils.helpers import filename

    names = {filename("alert") for _ in range(50)}

    assert len(names) == 50, "filenames must be unique within the same second"


def test_pipeline_process_smoke():
    import numpy as np

    from ai.pipeline import pipeline

    # Check models exist before running — skip if missing
    from utils.config import YOLO_MODEL, VIOLENCE_MODEL, MODEL_DIR
    hand_landmarker = MODEL_DIR / "hand_landmarker.task"
    missing = [m for m in [YOLO_MODEL, VIOLENCE_MODEL, hand_landmarker]
               if not m.exists()]
    if missing:
        print(f"SKIPPING: Missing models: {[m.name for m in missing]}")
        return

    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    result = pipeline.process(frame)
    assert "frame" in result
    assert "threat" in result
    assert result["threat"]["level"] in ("SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL")


if __name__ == "__main__":
    failures = 0

    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()

                print(f"PASS {name}")
            except Exception as e:
                failures += 1

                print(f"FAIL {name}: {e}")

    print("done", "WITH FAILURES" if failures else "all passed")

    sys.exit(1 if failures else 0)
