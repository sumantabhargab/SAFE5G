import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from utils.config import YOLO_MODEL, YOLO_CONFIDENCE
from ai.tracker import PersonTrackManager


class YOLODetector:
    """
    Unified YOLO detector used by the Safe5G pipeline.

    Returns a dictionary in the following format:

    {
        "frame": annotated_frame,
        "detections": [...],
        "person_count": int,
        "vehicle_count": int,
        "confidence": float,     # confidence of the most relevant detection
        "person_confidence": float,
        "fps": float,
        "track_ids": [int]       # active person track IDs
    }
    """

    VEHICLE_CLASSES = {
        "car",
        "truck",
        "bus",
        "motorcycle",
        "bicycle",
    }

    def __init__(self, model_path=YOLO_MODEL, confidence=YOLO_CONFIDENCE):
        model_path = Path(model_path)

        if not model_path.exists():
            self.ready = False
            raise FileNotFoundError(f"YOLO model not found: {model_path}")

        self.model = YOLO(str(model_path))

        self.class_names = self.model.names

        self.confidence_threshold = confidence

        self.ready = True

        self.last_time = time.time()

        self.frame_counter = 0

        self.fps = 0

        # ReID person tracker (loaded lazily on first detect call)
        self._tracker = None

    def _update_fps(self):
        self.frame_counter += 1

        current = time.time()

        elapsed = current - self.last_time

        if elapsed >= 1:
            self.fps = self.frame_counter / elapsed

            self.frame_counter = 0

            self.last_time = current

    def detect(self, frame, annotate=True):
        annotated = frame.copy() if annotate else frame

        detections = []

        person_count = 0

        vehicle_count = 0

        person_confidence = 0.0

        person_detections = []  # [x1,y1,x2,y2,conf] for tracker

        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
        )

        for result in results:
            for box in result.boxes:
                cls = int(box.cls.item())

                conf = float(box.conf.item())

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                label = self.class_names[cls]

                if label == "person":
                    person_count += 1

                    person_confidence = max(person_confidence, conf)

                    person_detections.append([x1, y1, x2, y2, conf])

                if label in self.VEHICLE_CLASSES:
                    vehicle_count += 1

                detections.append(
                    {
                        "label": label,
                        "confidence": conf,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    }
                )

                if annotate:
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    cv2.putText(
                        annotated,
                        f"{label} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

        # ReID tracking — assign stable IDs to persons
        track_ids = []

        if person_detections:
            if self._tracker is None:
                self._tracker = PersonTrackManager()

            tracks = self._tracker.update(annotated, person_detections)

            track_map = {}  # (x1,y1,x2,y2) -> track

            for track in tracks:
                track_map[(track.x1, track.y1, track.x2, track.y2)] = track
                track_ids.append(track.track_id)

                if annotate:
                    color = (0, 255, 0)  # green default
                    # Color-code by track_id for visual distinction
                    hue = (track.track_id * 37) % 256
                    color = self._track_id_to_color(hue)

                    # ID label above bbox
                    id_text = f"ID:{track.track_id}"

                    id_x = int(track.x1)
                    id_y = int(track.y1) - 5

                    cv2.rectangle(
                        annotated,
                        (id_x - 2, id_y - 14),
                        (id_x + len(id_text) * 8 + 4, id_y + 2),
                        color,
                        -1,
                    )

                    cv2.putText(
                        annotated,
                        id_text,
                        (id_x, id_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 255, 255),
                        1,
                    )

        self._update_fps()

        return {
            "frame": annotated,
            "detections": detections,
            "person_count": person_count,
            "vehicle_count": vehicle_count,
            "confidence": person_confidence,
            "person_confidence": person_confidence,
            "fps": self.fps,
            "track_ids": track_ids,
        }

    @staticmethod
    def _track_id_to_color(hue):
        """Map a hue value (0-255) to a BGR color for visual ID distinction."""
        # Simple HSV -> BGR conversion for distinct colors per track
        s = 255
        v = 255
        # Use OpenCV HSV->BGR conversion
        color = cv2.cvtColor(
            np.uint8([[[hue, s, v]]]),
            cv2.COLOR_HSV2BGR,
        )[0][0]
        return tuple(int(c) for c in color)


yolo_detector = YOLODetector()
