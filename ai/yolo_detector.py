from ultralytics import YOLO
import cv2
import time
from pathlib import Path


class YOLODetector:
    """
    Unified YOLO detector used by the Safe5G pipeline.

    Returns a dictionary in the following format:

    {
        "frame": annotated_frame,
        "detections": [...],
        "person_count": int,
        "vehicle_count": int,
        "confidence": float,
        "fps": float
    }
    """

    VEHICLE_CLASSES = {
        "car",
        "truck",
        "bus",
        "motorcycle",
        "bicycle"
    }

    def __init__(

        self,

        model_path="models/yolov8n.pt",

        confidence=0.4

    ):

        model_path = Path(model_path)

        if not model_path.exists():

            raise FileNotFoundError(

                f"YOLO model not found: {model_path}"

            )

        self.model = YOLO(str(model_path))

        self.class_names = self.model.names

        self.confidence_threshold = confidence

        self.last_time = time.time()

        self.frame_counter = 0

        self.fps = 0

    def _update_fps(self):

        self.frame_counter += 1

        current = time.time()

        elapsed = current - self.last_time

        if elapsed >= 1:

            self.fps = self.frame_counter / elapsed

            self.frame_counter = 0

            self.last_time = current

    def detect(

        self,

        frame

    ):

        annotated = frame.copy()

        detections = []

        person_count = 0

        vehicle_count = 0

        highest_confidence = 0.0

        results = self.model.predict(

            source=frame,

            conf=self.confidence_threshold,

            verbose=False

        )

        for result in results:

            for box in result.boxes:

                cls = int(box.cls.item())

                conf = float(box.conf.item())

                x1, y1, x2, y2 = map(

                    int,

                    box.xyxy[0]

                )

                label = self.class_names[cls]

                highest_confidence = max(

                    highest_confidence,

                    conf

                )

                if label == "person":

                    person_count += 1

                if label in self.VEHICLE_CLASSES:

                    vehicle_count += 1

                detections.append({

                    "label": label,

                    "confidence": conf,

                    "x1": x1,

                    "y1": y1,

                    "x2": x2,

                    "y2": y2

                })

                color = (

                    0,

                    255,

                    0

                )

                cv2.rectangle(

                    annotated,

                    (x1, y1),

                    (x2, y2),

                    color,

                    2

                )

                cv2.putText(

                    annotated,

                    f"{label} {conf:.2f}",

                    (x1, y1 - 10),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.6,

                    color,

                    2

                )

        self._update_fps()

        cv2.putText(

            annotated,

            f"FPS : {self.fps:.1f}",

            (15, 30),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (255, 255, 0),

            2

        )

        return {

            "frame": annotated,

            "detections": detections,

            "person_count": person_count,

            "vehicle_count": vehicle_count,

            "confidence": highest_confidence,

            "fps": self.fps

        }


yolo_detector = YOLODetector()