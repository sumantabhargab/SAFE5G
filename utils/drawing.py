"""
====================================================
Safe5G Drawing Utilities
====================================================
Responsible for drawing everything on the frame.
"""

import cv2
import config


class Drawer:

    @staticmethod
    def draw_person(frame, person):

        x1, y1, x2, y2 = person.bbox

        if person.status == "SAFE":
            color = config.GREEN

        elif person.status == "LOW":
            color = (0, 255, 255)

        elif person.status == "MEDIUM":
            color = (0, 165, 255)

        elif person.status == "HIGH":
            color = (0, 69, 255)

        else:
            color = config.RED

        # Bounding Box
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        # Center Point
        cv2.circle(
            frame,
            person.center,
            5,
            config.RED,
            -1
        )

        # ID
        cv2.putText(
            frame,
            f"ID {person.id}",
            (x1, y1 - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

        # Threat Score
        cv2.putText(
            frame,
            f"Threat: {person.threat_score}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2
        )

        # Status
        cv2.putText(
            frame,
            person.status,
            (x1, y2 + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    @staticmethod
    def draw_statistics(frame, people_count, fps):

        cv2.putText(
            frame,
            "SAFE5G",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            config.YELLOW,
            2
        )

        cv2.putText(
            frame,
            f"People : {people_count}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            config.BLUE,
            2
        )

        cv2.putText(
            frame,
            f"FPS : {int(fps)}",
            (20, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            config.BLUE,
            2
        )

    @staticmethod
    def draw_zone(frame, zone):

        cv2.polylines(
            frame,
            [zone],
            True,
            config.YELLOW,
            2
        )

    @staticmethod
    def draw_line(frame, p1, p2):

        cv2.line(
            frame,
            p1,
            p2,
            config.BLUE,
            2
        )