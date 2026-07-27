import cv2
import threading

from ai.pipeline import pipeline
from camera.camera_manager import camera_manager
from web.app import app


class Safe5G:

    def __init__(self):

        self.running = True

    ############################################################
    # DASHBOARD
    ############################################################

    def start_dashboard(self):

        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False
        )

    ############################################################
    # CAMERA LOOP
    ############################################################

    def start_camera(self):

        cap = camera_manager.get_camera(0)

        while self.running:

            ret, frame = cap.read()

            if not ret:
                break

            # Run AI Pipeline
            result = pipeline.process(
                frame,
                camera="Camera 01",
                location="Main Gate"
            )

            # Send processed frame to website
            camera_manager.update_frame(result["frame"])

            # Optional OpenCV window
            cv2.imshow(
                "Safe5G",
                result["frame"]
            )

            key = cv2.waitKey(1)

            if key == ord("q"):
                self.running = False
                break

        pipeline.stop()
        camera_manager.release()
        cv2.destroyAllWindows()

    ############################################################
    # START APPLICATION
    ############################################################

    def run(self):

        dashboard = threading.Thread(
            target=self.start_dashboard,
            daemon=True
        )

        dashboard.start()

        self.start_camera()


if __name__ == "__main__":
    Safe5G().run()