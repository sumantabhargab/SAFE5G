import threading

import cv2

from utils.config import FRAME_WIDTH, FRAME_HEIGHT


class CameraManager:

    def __init__(self):
        self.cameras = {}

        self._lock = threading.Lock()

        # Latest processed frame from the AI pipeline
        self._latest_frame = None

        self._frame_version = 0

    #########################################################
    # CAMERA
    #########################################################

    def get_camera(self, index=0):
        with self._lock:
            if index not in self.cameras:
                cap = cv2.VideoCapture(index)

                if not cap.isOpened():
                    return None

                cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)

                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

                self.cameras[index] = cap

            return self.cameras[index]

    #########################################################
    # RAW FRAME
    #########################################################

    def read_frame(self, index=0):
        cap = self.get_camera(index)

        if cap is None:
            return None

        success, frame = cap.read()

        if not success:
            return None

        return frame

    #########################################################
    # UPDATE FRAME FOR DASHBOARD
    #########################################################

    def update_frame(self, frame):
        with self._lock:
            self._latest_frame = frame

            self._frame_version += 1

    #########################################################
    # JPEG FOR WEBSITE
    #########################################################

    def get_jpeg(self):
        with self._lock:
            frame = self._latest_frame

            if frame is None:
                return None

            frame = frame.copy()  # copy under lock, encode outside

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            return None

        return buffer.tobytes()

    #########################################################
    # MJPEG STREAM
    #########################################################

    def generate_frames(self):
        last_version = -1

        while True:
            with self._lock:
                frame = self._latest_frame

                version = self._frame_version

            if frame is None or version == last_version:
                import time

                time.sleep(0.05)

                continue

            last_version = version

            success, buffer = cv2.imencode(".jpg", frame.copy())

            if not success:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )

    #########################################################
    # RELEASE
    #########################################################

    def release(self):
        with self._lock:
            for cap in self.cameras.values():
                cap.release()

            self.cameras.clear()


camera_manager = CameraManager()
