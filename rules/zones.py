"""
====================================================
Safe5G Zones
====================================================

Contains restricted zones.

Coordinates are in image pixels.

These can later be loaded from JSON.
"""

import cv2


class Zone:

    def __init__(self, name, points):

        self.name = name

        self.points = points

    def contains(self, point):

        return cv2.pointPolygonTest(
            self.points,
            point,
            False
        ) >= 0


class ZoneManager:

    def __init__(self):

        self.zones = []

        self.load_default()

    def load_default(self):

        """
        Example restricted area.

        Change coordinates according
        to your webcam.
        """

        restricted = Zone(

            "Restricted",

            cv2.UMat(
                __import__("numpy").array([
                    [900, 120],
                    [1250, 120],
                    [1250, 650],
                    [900, 650]
                ], dtype="int32")
            ).get()

        )

        self.zones.append(restricted)

    def get_active_zone(self, point):

        for zone in self.zones:

            if zone.contains(point):

                return zone

        return None