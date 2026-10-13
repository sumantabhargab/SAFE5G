import json
import time
from pathlib import Path

WEIGHTS_FILE = Path(__file__).parent / "weights.json"


def _load_weights():
    """
    Load rule weights from weights.json when available; fall back to the
    built-in defaults that match rule_engine's original behaviour.
    """
    defaults = {
        "sos_gesture": 45,
        "persistent_gesture": 10,
        "violence": 25,
        "gesture_confidence_tiers": [10, 8, 5],
        "violence_confidence_tiers": [10, 7],
        "cooldown_seconds": 10,
        "trigger_score": 75,
    }

    try:
        data = json.loads(WEIGHTS_FILE.read_text())

        # alert_cooldown is now managed by AlertManager, not here
        # panic_button directly maps to sos_gesture score
        if isinstance(data.get("panic_button"), (int, float)):
            defaults["sos_gesture"] = data["panic_button"]
    except Exception:
        pass

    return defaults


def _to_percent(confidence):
    """
    Normalize a confidence input to 0-100. Accepts 0-1 floats (model
    probabilities, YOLO confidences) and 0-100 values alike.
    """
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return 0.0

    if value <= 1.0:
        return value * 100.0

    return min(value, 100.0)


class RuleEngine:
    """
    Temporal threat scoring and alert gating.

    This is the single authority for threat level (SAFE..CRITICAL) and for
    deciding when an alert fires. Confidence inputs are normalized to 0-100
    internally, so callers may pass 0-1 probabilities directly.
    """

    def __init__(self):
        self.weights = _load_weights()

        # Frame counters
        self.gesture_frames = 0
        self.violence_frames = 0
        self.person_frames = 0
        self.vehicle_frames = 0

        # Threat smoothing
        self.previous_score = 0

    def evaluate(
        self,
        help_gesture=False,
        violence=False,
        person_count=0,
        vehicle_count=0,
        gesture_confidence=0,
        violence_confidence=0,
    ):
        gesture_confidence = _to_percent(gesture_confidence)

        violence_confidence = _to_percent(violence_confidence)

        ###############################################
        # Temporal Counters
        ###############################################

        if help_gesture:
            self.gesture_frames = min(self.gesture_frames + 1, 30)
        else:
            self.gesture_frames = max(self.gesture_frames - 2, 0)

        if violence:
            self.violence_frames = min(self.violence_frames + 1, 30)
        else:
            self.violence_frames = max(self.violence_frames - 1, 0)

        if person_count > 0:
            self.person_frames = min(self.person_frames + 1, 30)
        else:
            self.person_frames = max(self.person_frames - 1, 0)

        if vehicle_count > 0:
            self.vehicle_frames = min(self.vehicle_frames + 1, 30)
        else:
            self.vehicle_frames = max(self.vehicle_frames - 1, 0)

        ###############################################
        # Threat Score
        ###############################################

        score = 0

        reasons = []

        # SOS Gesture (highest priority)
        if self.gesture_frames >= 15:
            score += self.weights["sos_gesture"]
            reasons.append("SOS Gesture")

        # Gesture Confidence
        g_tiers = self.weights["gesture_confidence_tiers"]
        if self.gesture_frames > 0 and gesture_confidence >= 95:
            score += g_tiers[0]
        elif self.gesture_frames > 0 and gesture_confidence >= 85:
            score += g_tiers[1]
        elif self.gesture_frames > 0 and gesture_confidence >= 75:
            score += g_tiers[2]

        # Violence
        if self.violence_frames >= 10:
            score += self.weights["violence"]
            reasons.append("Violence")

        v_tiers = self.weights["violence_confidence_tiers"]
        if self.violence_frames > 0 and violence_confidence >= 90:
            score += v_tiers[0]
        elif self.violence_frames > 0 and violence_confidence >= 80:
            score += v_tiers[1]

        # Persons (crowd)
        if person_count >= 5:
            score += 10
            reasons.append("Crowd")
        elif person_count >= 3:
            score += 8
        elif person_count >= 2:
            score += 5
        elif person_count == 1:
            score += 2

        # Vehicles (traffic)
        if vehicle_count >= 3:
            score += 5
            reasons.append("Traffic")
        elif vehicle_count >= 1:
            score += 2

        # Long Gesture Bonus
        if self.gesture_frames >= 25:
            score += self.weights["persistent_gesture"]
            reasons.append("Persistent Gesture")

        ###############################################
        # Smooth Threat Score
        ###############################################

        score = 0.75 * self.previous_score + 0.25 * score

        self.previous_score = score

        score = min(round(score), 100)

        ###############################################
        # Threat Level
        ###############################################

        if score < 30:
            level = "SAFE"
        elif score < 50:
            level = "LOW"
        elif score < 70:
            level = "MEDIUM"
        elif score < 90:
            level = "HIGH"
        else:
            level = "CRITICAL"

        ###############################################
        # Trigger Logic
        ###############################################

        # Trigger on score threshold only. Actual alert dispatch is
        # gated by AlertManager's cooldown (config.ALERT_COOLDOWN).
        trigger = score >= self.weights["trigger_score"]

        return {
            "trigger": trigger,
            "score": score,
            "level": level,
            "reasons": reasons,
            "gesture_frames": self.gesture_frames,
            "violence_frames": self.violence_frames,
            "person_count": person_count,
            "vehicle_count": vehicle_count,
        }

    def reset(self):
        self.gesture_frames = 0
        self.violence_frames = 0
        self.person_frames = 0
        self.vehicle_frames = 0
        self.previous_score = 0


rule_engine = RuleEngine()
