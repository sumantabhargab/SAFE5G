import time

import cv2

from ai.yolo_detector import yolo_detector
from ai.gesture_detector import gesture_detector
from ai.violence_detector import violence_detector
from rules.rule_engine import rule_engine
from sensors.sos_trigger import sos_trigger
from media.save_media import media_manager
from utils.helpers import draw_banner, overlay
from utils.config import THREAT_COLORS, ALERT_COOLDOWN


class AIPipeline:
    """
    Per-frame orchestrator.

    Flow: YOLO -> gesture -> violence -> RuleEngine (threat scoring +
    cooldown-gated trigger) -> alert dispatch -> recording -> HUD.

    All detections and the trigger decision are reported back to the caller
    so the dashboard can display real system state.
    """

    def __init__(self):
        self.recording = False

        self.frame_counter = 0

        self.frames_since_alert = 0

        self.last_trigger = None  # dict describing the last fired alert

        self.last_threat = {"score": 0, "level": "SAFE", "reasons": []}

        self.last_violence = None

    def process(self, frame, camera="Camera 01", location="Unknown"):
        #############################################
        # YOLO
        #############################################

        yolo = yolo_detector.detect(frame)

        output = yolo["frame"]

        detections = yolo["detections"]

        person_count = yolo["person_count"]

        vehicle_count = yolo["vehicle_count"]

        person_confidence = yolo["person_confidence"]

        #############################################
        # Gesture Detection
        #############################################

        gesture = gesture_detector.detect(output)

        output = gesture["frame"]

        help_detected = gesture["help"]

        gesture_frames = gesture["frames"]

        # Gesture "confidence": fraction of the confirmation requirement
        # reached (0..1) -- palm present means landmarks were found this frame
        gesture_confidence = 1.0 if gesture_frames > 0 else 0.0

        #############################################
        # Violence Detection (trained classifier + window voting)
        # Classify every other frame to keep CPU framerate usable; the
        # window voting absorbs the gap.
        #############################################

        self.frame_counter += 1

        if self.frame_counter % 2 == 0 or self.last_violence is None:
            violence = violence_detector.detect(output)

            self.last_violence = violence
        else:
            violence = self.last_violence

        output = violence["frame"]

        violence_detected = violence["violence"]

        violence_confidence = violence["score"]

        #############################################
        # Rule Engine (threat scoring + trigger decision)
        #############################################

        verdict = rule_engine.evaluate(
            help_gesture=help_detected,
            violence=violence_detected,
            person_count=person_count,
            vehicle_count=vehicle_count,
            gesture_confidence=gesture_confidence,
            violence_confidence=violence_confidence,
        )

        self.last_threat = verdict

        self.last_person_count = person_count

        #############################################
        # Alert Dispatch (cooldown-gated by rule engine + alert manager)
        #############################################

        self.frames_since_alert += 1

        fired = False

        if verdict["trigger"]:
            # Direct escalation path: rule engine says fire. alert_manager
            # applies its own per-type cooldown as a second gate.
            if help_detected:
                alert = sos_trigger.help_detected(
                    output,
                    round(violence_confidence, 3) if not gesture_confidence else 1.0,
                    camera,
                    location,
                    threat_level=verdict["level"],
                )
            elif violence_detected:
                alert = sos_trigger.violence_detected(
                    output,
                    violence_confidence,
                    camera,
                    location,
                    threat_level=verdict["level"],
                )
            else:
                alert = sos_trigger.activate(
                    {
                        "type": "Threat Level HIGH",
                        "confidence": verdict["score"] / 100.0,
                        "camera": camera,
                        "location": location,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "image": "",
                        "threat_level": verdict["level"],
                    },
                    output,
                )

            if alert is not None:
                fired = True

                self.last_trigger = alert

                self.frames_since_alert = 0

                draw_banner(
                    output,
                    f"{alert['type'].upper()} - THREAT {verdict['level']}",
                )

        #############################################
        # Recording (start on trigger, stop after cooldown of quiet)
        #############################################

        if fired and not self.recording:
            h, w = output.shape[:2]

            media_manager.start_recording(w, h, 20)

            self.recording = True

        if self.recording:
            media_manager.write(output)

            # Stop recording after the threat has subsided for a while
            if verdict["score"] < 30 and self.frames_since_alert > 5 * 30:
                media_manager.stop_recording()

                self.recording = False

        #############################################
        # Dashboard Overlay + HUD
        #############################################

        overlay(output)

        color = THREAT_COLORS.get(verdict["level"], (255, 255, 255))

        cv2.putText(
            output,
            f"FPS : {yolo['fps']:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            output,
            f"Persons : {person_count}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        cv2.putText(
            output,
            f"Vehicles : {vehicle_count}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        cv2.putText(
            output,
            f"Threat : {verdict['level']} ({verdict['score']})",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
        )

        return {
            "frame": output,
            "detections": detections,
            "persons": person_count,
            "vehicles": vehicle_count,
            "help": help_detected,
            "gesture_frames": gesture_frames,
            "violence": violence_detected,
            "violence_confidence": violence_confidence,
            "window_votes": violence["window_votes"],
            "confidence": person_confidence,
            "threat": verdict,
            "alert_fired": fired,
            "fps": yolo["fps"],
        }

    def stop(self):
        if self.recording:
            media_manager.stop_recording()

            self.recording = False


pipeline = AIPipeline()
