import cv2
import math

from mediapipe.python.solutions import hands
from mediapipe.python.solutions import drawing_utils


class GestureDetector:
    """
    Gesture detector for Safe5G.

    Current help gesture:
        Open palm (5 fingers extended)

    Returns:
    {
        "help": bool,
        "landmarks": list,
        "frame": annotated_frame
    }
    """

    def __init__(self):

        self.mp_hands = hands

        self.drawer = drawing_utils

        self.hand_detector = hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5
        )

    def finger_up(self, tip, pip):
        return tip.y < pip.y

    def detect(self, frame):

        annotated = frame.copy()

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = self.hand_detector.process(rgb)

        help_detected = False

        landmark_points = []

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                self.drawer.draw_landmarks(
                    annotated,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

                lm = hand_landmarks.landmark

                thumb = lm[4].x > lm[3].x

                index = self.finger_up(lm[8], lm[6])

                middle = self.finger_up(lm[12], lm[10])

                ring = self.finger_up(lm[16], lm[14])

                pinky = self.finger_up(lm[20], lm[18])

                if thumb and index and middle and ring and pinky:

                    help_detected = True

                for p in lm:

                    landmark_points.append(
                        (p.x, p.y)
                    )

        if help_detected:

            cv2.putText(
                annotated,
                "HELP GESTURE DETECTED",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                3
            )

        return {

            "help": help_detected,

            "landmarks": landmark_points,

            "frame": annotated

        }


gesture_detector = GestureDetector()