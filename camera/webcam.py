"""
====================================================
Safe5G Webcam Module
====================================================

Responsible for:

- Opening webcam
- Reading frames
- Releasing webcam
- Camera configuration

This module NEVER performs AI inference.
"""

import cv2

import config


class Webcam:

    def __init__(self):

        self.cap = None

    def start(self):

        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)

        if not self.cap.isOpened():
            raise RuntimeError("Unable to open webcam.")

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            config.FRAME_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            config.FRAME_HEIGHT
        )

        print("====================================")
        print(" Safe5G Webcam Started")
        print("====================================")

    def read(self):

        if self.cap is None:
            return None

        success, frame = self.cap.read()

        if not success:
            return None

        return frame

    def is_open(self):

        if self.cap is None:
            return False

        return self.cap.isOpened()

    def stop(self):

        if self.cap is not None:
            self.cap.release()

        cv2.destroyAllWindows()

        print("====================================")
        print(" Webcam Closed")
        print("====================================")