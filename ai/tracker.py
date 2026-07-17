"""
====================================================
Safe5G Tracker
====================================================

Uses Ultralytics ByteTrack.

Input:
    Video Frame

Output:
    List[TrackedPerson]
"""

from ultralytics import YOLO

import config

from ai.person import TrackedPerson
from ai.detection import Detection


class Tracker:

    def __init__(self):

        self.model = YOLO(str(config.YOLO_MODEL))

        self.people = {}

    def update(self, frame):

        results = self.model.track(

            frame,

            persist=True,

            tracker="bytetrack.yaml",

            conf=config.CONFIDENCE_THRESHOLD,

            verbose=False

        )

        tracked_people = []

        if len(results) == 0:

            return tracked_people

        boxes = results[0].boxes

        if boxes.id is None:

            return tracked_people

        ids = boxes.id.int().cpu().tolist()

        xyxy = boxes.xyxy.cpu().tolist()

        confs = boxes.conf.cpu().tolist()

        clss = boxes.cls.int().cpu().tolist()

        for track_id, bbox, conf, cls in zip(ids, xyxy, confs, clss):

            if cls != config.PERSON_CLASS_ID:
                continue

            detection = Detection(

                bbox=tuple(map(int, bbox)),

                confidence=float(conf)

            )

            if track_id in self.people:

                person = self.people[track_id]

                person.update(detection)

            else:

                person = TrackedPerson(

                    track_id,

                    detection

                )

                self.people[track_id] = person

            tracked_people.append(person)

        return tracked_people