"""
====================================================
YOLO Detector
====================================================

Runs YOLOv8 inference.

Returns a list of Detection objects.

NO tracking happens here.
"""

from ultralytics import YOLO

import config

from ai.detection import Detection


class Detector:

    def __init__(self):

        print("Loading YOLO Model...")

        self.model = YOLO(str(config.YOLO_MODEL))

        print("YOLO Loaded Successfully")

    # -------------------------------------------------

    def detect(self, frame):

        results = self.model(

            frame,

            conf=config.CONFIDENCE_THRESHOLD,

            verbose=False

        )

        detections = []

        for box in results[0].boxes:

            cls = int(box.cls[0])

            if cls != config.PERSON_CLASS_ID:
                continue

            x1, y1, x2, y2 = map(

                int,

                box.xyxy[0]

            )

            confidence = float(

                box.conf[0]

            )

            detections.append(

                Detection(

                    bbox=(x1, y1, x2, y2),

                    confidence=confidence

                )

            )

        return detections