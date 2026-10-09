"""
SAFE5G core tests.

Run from the project root:  python -m pytest tests/ -q
(or: python tests/test_core.py)
"""

import sys
import os
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


def test_rule_engine_trigger_and_cooldown():
    import time

    from rules.rule_engine import RuleEngine

    engine = RuleEngine()

    engine.cooldown = 1.0

    triggered_at = None

    for i in range(100):
        out = engine.evaluate(
            help_gesture=True,
            violence=False,
            person_count=1,
            gesture_confidence=1.0,
        )

        if out["trigger"]:
            triggered_at = i

            break

    assert triggered_at is not None, "sustained gesture must eventually trigger"

    # Cooldown: immediately-repeated evaluation must not trigger again
    out = engine.evaluate(
        help_gesture=True,
        violence=False,
        person_count=1,
        gesture_confidence=1.0,
    )

    assert not out["trigger"], "cooldown must suppress immediate re-trigger"

    time.sleep(1.1)

    out = engine.evaluate(
        help_gesture=True,
        violence=False,
        person_count=1,
        gesture_confidence=1.0,
    )

    assert out["trigger"], "cooldown expiry must allow re-trigger"


def test_database_roundtrip():
    import tempfile

    from database.database import Database

    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "test.db")

        alert_id = db.add_alert(
            "Violence", 0.9, "Cam 1", "Test", "", "Pending"
        )

        rows = db.recent_alerts(limit=5)

        assert rows and rows[0]["id"] == alert_id

        assert rows[0]["alert_type"] == "Violence"

        db.update_status(alert_id, "Resolved")

        assert db.total_resolved() == 1

        db.delete_alert(alert_id)

        assert db.total_alerts() == 0

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


def test_config_has_colors():
    from utils import config

    # Regression: drawing.py crashed on missing GREEN/RED/YELLOW/BLUE
    for name in ("GREEN", "RED", "YELLOW", "BLUE", "THREAT_COLORS"):
        assert hasattr(config, name), f"config.{name} missing"


def test_filename_unique_within_second():
    from utils.helpers import filename

    names = {filename("alert") for _ in range(50)}

    assert len(names) == 50, "filenames must be unique within the same second"


def test_pipeline_process_smoke():
    import numpy as np

    from ai.pipeline import pipeline

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
