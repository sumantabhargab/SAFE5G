import cv2
import numpy as np


class ViolenceDetector:
    """
    Lightweight violence detector.

    This implementation is intentionally modular.

    Current version:
        • Motion-based heuristic
        • Designed as a placeholder

    Future upgrades:
        ✓ MoBiLSTM
        ✓ ConvLSTM
        ✓ I3D
        ✓ SlowFast
        ✓ Video Swin Transformer

    Pipeline will NOT need any changes when the
    model is upgraded.
    """

    def __init__(self, motion_threshold=35):

        self.previous_gray = None

        self.motion_threshold = motion_threshold

    def detect(self, frame):

        annotated = frame.copy()

        gray = cv2.cvtColor(

            frame,

            cv2.COLOR_BGR2GRAY

        )

        gray = cv2.GaussianBlur(

            gray,

            (21, 21),

            0

        )

        violence = False

        score = 0.0

        if self.previous_gray is not None:

            delta = cv2.absdiff(

                self.previous_gray,

                gray

            )

            thresh = cv2.threshold(

                delta,

                25,

                255,

                cv2.THRESH_BINARY

            )[1]

            thresh = cv2.dilate(

                thresh,

                None,

                iterations=2

            )

            motion_pixels = np.sum(

                thresh == 255

            )

            total_pixels = thresh.shape[0] * thresh.shape[1]

            score = motion_pixels / total_pixels

            if score > 0.12:

                violence = True

        self.previous_gray = gray

        if violence:

            cv2.putText(

                annotated,

                "VIOLENCE DETECTED",

                (20, 110),

                cv2.FONT_HERSHEY_SIMPLEX,

                1,

                (0, 0, 255),

                3

            )

        return {

            "violence": violence,

            "score": round(score, 3),

            "frame": annotated

        }

    def reset(self):

        self.previous_gray = None


violence_detector = ViolenceDetector()