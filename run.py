import cv2
import threading
import time

from ai.pipeline import pipeline
from camera.camera_manager import camera_manager
from utils.config import CAMERAS, CAMERA_INDEX
from web.app import app


class Safe5G:

    def __init__(self):
        self.running = True

    ############################################################
    # DASHBOARD
    ############################################################

    def start_dashboard(self):
        app.run(
            host="127.0.0.1",
            port=5000,
            debug=False,
            use_reloader=False,
        )

    ############################################################
    # CAMERA LOOP
    ############################################################

    def start_camera(self):
        cap = camera_manager.get_camera(CAMERA_INDEX)

        if cap is None or not cap.isOpened():
            print(f"[ERROR] Camera {CAMERA_INDEX} could not be opened. "
                  f"Dashboard is still running at http://127.0.0.1:5000")

            return

        cam_id = next(iter(CAMERAS))

        cam_name = CAMERAS[cam_id]["name"]

        location = CAMERAS[cam_id]["location"]

        consecutive_failures = 0

        while self.running:
            ret, frame = cap.read()

            if not ret or frame is None:
                consecutive_failures += 1

                if consecutive_failures > 30:
                    print("[ERROR] Camera stream lost. Exiting.")

                    break

                time.sleep(0.1)

                continue

            consecutive_failures = 0

            try:
                result = pipeline.process(
                    frame,
                    camera=cam_name,
                    location=location,
                )
            except Exception as e:
                print(f"[ERROR] pipeline failure: {e}")

                continue

            # Send processed frame to the website
            camera_manager.update_frame(result["frame"])

            # Optional OpenCV window
            cv2.imshow("Safe5G", result["frame"])

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
            daemon=True,
        )

        dashboard.start()

        self.start_camera()


if __name__ == "__main__":
    Safe5G().run()
