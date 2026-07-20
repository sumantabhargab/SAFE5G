import cv2


class CameraManager:

    def __init__(self):

        self.cameras = {}

        # Latest processed frame from the AI pipeline
        self.latest_frame = None

    #########################################################
    # CAMERA
    #########################################################

    def get_camera(self, index=0):

        if index not in self.cameras:

            cap = cv2.VideoCapture(index)

            if not cap.isOpened():

                raise RuntimeError(f"Cannot open camera {index}")

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            self.cameras[index] = cap

        return self.cameras[index]

    #########################################################
    # RAW FRAME
    #########################################################

    def read_frame(self, index=0):

        cap = self.get_camera(index)

        success, frame = cap.read()

        if not success:
            return None

        return frame

    #########################################################
    # UPDATE FRAME FOR DASHBOARD
    #########################################################

    def update_frame(self, frame):

        self.latest_frame = frame.copy()

    #########################################################
    # JPEG FOR WEBSITE
    #########################################################

    def get_jpeg(self):

        if self.latest_frame is None:
            return None

        success, buffer = cv2.imencode(".jpg", self.latest_frame)

        if not success:
            return None

        return buffer.tobytes()

    #########################################################
    # MJPEG STREAM
    #########################################################

    def generate_frames(self):

        while True:

            jpg = self.get_jpeg()

            if jpg is None:
                continue

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                jpg +
                b'\r\n'
            )

    #########################################################
    # RELEASE
    #########################################################

    def release(self):

        for cap in self.cameras.values():

            cap.release()

        self.cameras.clear()


camera_manager = CameraManager()