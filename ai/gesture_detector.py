import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision

from utils.config import GESTURE_CONFIRM_FRAMES, MODEL_DIR


class GestureDetector:
    """
    Gesture detector for Safe5G.

    Help gesture:
        Open palm (all 5 fingers extended), held steady.

    Handedness-aware finger logic (works for left and right hands and for
    mirrored camera images) plus temporal confirmation: the gesture must be
    present in GESTURE_CONFIRM_FRAMES consecutive frames to be reported.

    Uses the MediaPipe Tasks HandLandmarker API (works on mediapipe >= 0.10).

    Returns:
    {
        "help": bool,
        "frames": int,       # consecutive confirmation frames
        "hands": int,
        "landmarks": list,
        "frame": annotated_frame
    }
    """

    # Landmark indices: (tip, pip) pairs for thumb, index, middle, ring, pinky
    FINGER_JOINTS = [(4, 3), (8, 6), (12, 10), (16, 14), (20, 18)]

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),           # thumb
        (0, 5), (5, 6), (6, 7), (7, 8),           # index
        (5, 9), (9, 10), (10, 11), (11, 12),      # middle
        (9, 13), (13, 14), (14, 15), (15, 16),    # ring
        (13, 17), (17, 18), (18, 19), (19, 20),   # pinky
        (0, 17),
    ]

    def __init__(self):
        model_path = MODEL_DIR / "hand_landmarker.task"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Hand landmarker model not found: {model_path}\n"
                "Download: https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            )

        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.landmarker = vision.HandLandmarker.create_from_options(options)

        self._timestamp_ms = 0

        self.confirm_frames = 0

    def _open_palm(self, lm, handedness_label):
        """
        Check whether one hand's landmarks form an open palm.

        Distance-from-wrist logic is orientation-independent (unlike
        y-coordinate comparisons, which break when the hand is rotated).
        The thumb is checked with the handedness label from MediaPipe.
        """
        wrist = lm[0]

        fingers_up = 0

        for tip_idx, pip_idx in self.FINGER_JOINTS[1:]:
            tip = lm[tip_idx]

            pip = lm[pip_idx]

            d_tip = (tip.x - wrist.x) ** 2 + (tip.y - wrist.y) ** 2

            d_pip = (pip.x - wrist.x) ** 2 + (pip.y - wrist.y) ** 2

            if d_tip > d_pip * 1.1:  # margin against jitter
                fingers_up += 1

        # Thumb: extended when tip is farther from index MCP (lm[5]) than the
        # IP joint is, on the correct side for the detected hand.
        thumb_tip = lm[4]

        thumb_ip = lm[3]

        index_mcp = lm[5]

        if handedness_label == "Left":
            thumb_out = thumb_tip.x < thumb_ip.x
        else:
            thumb_out = thumb_tip.x > thumb_ip.x

        thumb_span = abs(thumb_tip.x - index_mcp.x) > abs(thumb_ip.x - index_mcp.x)

        thumb = thumb_out and thumb_span

        return fingers_up == 4 and thumb

    def detect(self, frame):
        annotated = frame.copy()

        self._timestamp_ms += 33  # ~30 fps monotonic timestamp for VIDEO mode

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
        )

        results = self.landmarker.detect_for_video(mp_image, self._timestamp_ms)

        palm_this_frame = False

        landmark_points = []

        if results.hand_landmarks:
            for hand_landmarks, hand_info in zip(
                results.hand_landmarks,
                results.handedness,
            ):
                label = hand_info[0].category_name

                self._draw_hand(annotated, hand_landmarks)

                if self._open_palm(hand_landmarks, label):
                    palm_this_frame = True

                for p in hand_landmarks:
                    landmark_points.append((p.x, p.y))

        # Temporal confirmation: require consecutive frames
        if palm_this_frame:
            self.confirm_frames += 1
        else:
            self.confirm_frames = 0

        help_detected = self.confirm_frames >= GESTURE_CONFIRM_FRAMES

        if help_detected:
            cv2.putText(
                annotated,
                "HELP GESTURE DETECTED",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                3,
            )

        return {
            "help": help_detected,
            "frames": self.confirm_frames,
            "hands": len(results.hand_landmarks) if results.hand_landmarks else 0,
            "landmarks": landmark_points,
            "frame": annotated,
        }

    def _draw_hand(self, frame, lm):
        h, w = frame.shape[:2]

        pts = [(int(p.x * w), int(p.y * h)) for p in lm]

        for a, b in self.HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)

        for p in pts:
            cv2.circle(frame, p, 4, (0, 0, 255), -1)

    def reset(self):
        self.confirm_frames = 0


gesture_detector = GestureDetector()
