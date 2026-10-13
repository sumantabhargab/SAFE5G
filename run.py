import cv2
import threading
import time
import signal
import sys

from ai.pipeline import pipeline
from camera.camera_manager import camera_manager
from utils.config import CAMERAS, CAMERA_INDEX, HEADLESS
from web.app import app


class Safe5G:

    def __init__(self):
        self.running = True

    ############################################################
    # SHUTDOWN HANDLERS
    ############################################################

    def shutdown_handler(self, signum, frame):
        from utils.logger import logger
        logger.info("Shutdown signal received (Ctrl-C). Stopping...")
        self.running = False
        pipeline.stop()
        camera_manager.release()

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
            from utils.logger import logger
            logger.error(f"Camera {CAMERA_INDEX} could not be opened. "
                         f"Dashboard is still running at http://127.0.0.1:5000")
            return

        cam_id = next(iter(CAMERAS))

        cam_name = CAMERAS[cam_id]["name"]

        location = CAMERAS[cam_id]["location"]

        consecutive_failures = 0

        retry_delay = 1.0

        while self.running:
            ret, frame = cap.read()

            if not ret or frame is None:
                consecutive_failures += 1

                if consecutive_failures <= 30:
                    time.sleep(min(retry_delay, 30))
                    retry_delay *= 2
                else:
                    logger.warning("Camera stream lost, retrying...")
                    time.sleep(30)
                    continue

                continue

            consecutive_failures = 0

            retry_delay = 1.0

            try:
                result = pipeline.process(
                    frame,
                    camera=cam_name,
                    location=location,
                )
            except Exception as e:
                from utils.logger import logger
                logger.error(f"pipeline failure: {e}")

                continue

            # Send processed frame to the website
            camera_manager.update_frame(result["frame"])

            # Optional OpenCV window (skip in headless mode)
            if not HEADLESS:
                cv2.imshow("Safe5G", result["frame"])

                key = cv2.waitKey(1)

                if key == ord("q"):
                    self.running = False

                    break

        pipeline.stop()

        camera_manager.release()

        if not HEADLESS:
            cv2.destroyAllWindows()

    ############################################################
    # START APPLICATION
    ############################################################

    def run(self):
        # Register shutdown handlers for graceful cleanup
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)

        dashboard = threading.Thread(
            target=self.start_dashboard,
            daemon=True,
        )

        dashboard.start()

        self.start_camera()


if __name__ == "__main__":
    Safe5G().run()
