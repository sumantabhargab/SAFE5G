import time


class RuleEngine:

    def __init__(self):

        # Frame counters
        self.gesture_frames = 0
        self.violence_frames = 0
        self.person_frames = 0
        self.vehicle_frames = 0

        # Threat smoothing
        self.previous_score = 0

        # Alert cooldown
        self.cooldown = 10  # seconds
        self.last_alert = 0

    #########################################################
    # MAIN DECISION ENGINE
    #########################################################

    def evaluate(

        self,

        help_gesture=False,

        violence=False,

        person_count=0,

        vehicle_count=0,

        gesture_confidence=0,

        violence_confidence=0,

    ):

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

        ################################################
        # SOS Gesture (Highest Priority)
        ################################################

        if self.gesture_frames >= 15:

            score += 45

            reasons.append("SOS Gesture")

        ################################################
        # Gesture Confidence
        ################################################

        if gesture_confidence >= 95:

            score += 10

        elif gesture_confidence >= 85:

            score += 8

        elif gesture_confidence >= 75:

            score += 5

        ################################################
        # Violence
        ################################################

        if self.violence_frames >= 10:

            score += 25

            reasons.append("Violence")

        if violence_confidence >= 90:

            score += 10

        elif violence_confidence >= 80:

            score += 7

        ################################################
        # Persons
        ################################################

        if person_count >= 5:

            score += 10

            reasons.append("Crowd")

        elif person_count >= 3:

            score += 8

        elif person_count >= 2:

            score += 5

        elif person_count == 1:

            score += 2

        ################################################
        # Vehicles
        ################################################

        if vehicle_count >= 3:

            score += 5

            reasons.append("Traffic")

        elif vehicle_count >= 1:

            score += 2

        ################################################
        # Long Gesture Bonus
        ################################################

        if self.gesture_frames >= 25:

            score += 10

            reasons.append("Persistent Gesture")

        ################################################
        # Smooth Threat Score
        ################################################

        score = 0.75 * self.previous_score + 0.25 * score

        self.previous_score = score

        score = min(round(score), 100)

        ################################################
        # Threat Level
        ################################################

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

        ################################################
        # Trigger Logic
        ################################################

        trigger = False

        now = time.time()

        if (

            score >= 75

            and

            (now - self.last_alert) > self.cooldown

        ):

            trigger = True

            self.last_alert = now

        ################################################
        # Return Result
        ################################################

        return {

            "trigger": trigger,

            "score": score,

            "level": level,

            "reasons": reasons,

            "gesture_frames": self.gesture_frames,

            "violence_frames": self.violence_frames,

            "person_count": person_count,

            "vehicle_count": vehicle_count

        }


rule_engine = RuleEngine()