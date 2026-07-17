"""
====================================================
Detection Object
====================================================

Represents one YOLO detection.

This class contains only information produced
directly from the detector.

Tracking information is NOT stored here.
"""

from dataclasses import dataclass


@dataclass
class Detection:

    bbox: tuple

    confidence: float

    @property
    def x1(self):
        return self.bbox[0]

    @property
    def y1(self):
        return self.bbox[1]

    @property
    def x2(self):
        return self.bbox[2]

    @property
    def y2(self):
        return self.bbox[3]

    @property
    def width(self):

        return self.x2 - self.x1

    @property
    def height(self):

        return self.y2 - self.y1

    @property
    def area(self):

        return self.width * self.height

    @property
    def center(self):

        cx = (self.x1 + self.x2) // 2

        cy = (self.y1 + self.y2) // 2

        return (cx, cy)

    def to_dict(self):

        return {

            "bbox": self.bbox,

            "confidence": self.confidence,

            "center": self.center

        }