"""
====================================================
Tracked Person Object
====================================================

Represents one tracked person inside Safe5G.

Every detected individual becomes a TrackedPerson.

This object stores:

- ID
- Bounding Box
- Center
- Velocity
- Threat Score
- Active Rules
- Time Information

Everything in Safe5G revolves around this object.
"""

import math
import time

from ai.detection import Detection


class TrackedPerson:

    def __init__(self, person_id: int, detection: Detection):

        self.id = person_id

        self.first_seen = time.time()

        self.last_seen = self.first_seen

        self.frames_seen = 1

        self.disappeared_frames = 0

        self.previous_center = detection.center

        self.velocity = 0.0

        self.direction = "UNKNOWN"

        self.threat_score = 0

        self.status = "SAFE"

        self.active_rules = []

        self.update(detection)

    # -------------------------------------------------

    def update(self, detection: Detection):

        old_center = self.previous_center

        self.bbox = detection.bbox

        self.confidence = detection.confidence

        self.center = detection.center

        self.last_seen = time.time()

        self.frames_seen += 1

        self.disappeared_frames = 0

        self.__calculate_velocity(old_center)

        self.__calculate_direction(old_center)

        self.previous_center = self.center

    # -------------------------------------------------

    def __calculate_velocity(self, old_center):

        dx = self.center[0] - old_center[0]

        dy = self.center[1] - old_center[1]

        self.velocity = math.sqrt(dx * dx + dy * dy)

    # -------------------------------------------------

    def __calculate_direction(self, old_center):

        dx = self.center[0] - old_center[0]

        dy = self.center[1] - old_center[1]

        if abs(dx) > abs(dy):

            if dx > 0:
                self.direction = "RIGHT"
            elif dx < 0:
                self.direction = "LEFT"

        else:

            if dy > 0:
                self.direction = "DOWN"
            elif dy < 0:
                self.direction = "UP"

    # -------------------------------------------------

    def add_rule(self, rule_name):

        if rule_name not in self.active_rules:

            self.active_rules.append(rule_name)

    # -------------------------------------------------

    def clear_rules(self):

        self.active_rules.clear()

    # -------------------------------------------------

    def set_threat(self, score):

        self.threat_score = score

        if score >= 90:
            self.status = "CRITICAL"

        elif score >= 75:
            self.status = "HIGH"

        elif score >= 50:
            self.status = "MEDIUM"

        elif score >= 25:
            self.status = "LOW"

        else:
            self.status = "SAFE"

    # -------------------------------------------------

    @property
    def time_seen(self):

        return round(

            self.last_seen - self.first_seen,

            2

        )

    # -------------------------------------------------

    def increment_disappeared(self):

        self.disappeared_frames += 1

    # -------------------------------------------------

    def to_dict(self):

        return {

            "id": self.id,

            "bbox": self.bbox,

            "center": self.center,

            "velocity": self.velocity,

            "direction": self.direction,

            "threat_score": self.threat_score,

            "status": self.status,

            "time_seen": self.time_seen,

            "rules": self.active_rules

        }