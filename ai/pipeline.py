import cv2
import time

from ai.yolo_detector import yolo_detector
from ai.gesture_detector import gesture_detector
from ai.violence_detector import violence_detector

from sensors.sos_trigger import sos_trigger
from media.save_media import media_manager

from utils.helpers import draw_banner, overlay


class AIPipeline:

    def __init__(self):

        self.recording = False

        self.frame_counter = 0

        self.start_time = time.time()

    def process(

        self,

        frame,

        camera="Camera 01",

        location="Unknown"

    ):

        output = frame.copy()

        #############################################
        # YOLO
        #############################################

        yolo = yolo_detector.detect(frame)

        output = yolo["frame"]

        detections = yolo["detections"]

        person_count = yolo["person_count"]

        vehicle_count = yolo["vehicle_count"]

        confidence = yolo["confidence"]

        #############################################
        # Gesture Detection
        #############################################

        gesture = gesture_detector.detect(output)

        output = gesture["frame"]

        help_detected = gesture["help"]

        #############################################
        # Violence Detection
        #############################################

        violence = violence_detector.detect(output)

        output = violence["frame"]

        violence_detected = violence["violence"]

        #############################################
        # Alert Logic
        #############################################

        if help_detected:

            draw_banner(

                output,

                "HELP GESTURE DETECTED"

            )

            sos_trigger.help_detected(

                output,

                confidence,

                camera,

                location

            )

        if violence_detected:

            draw_banner(

                output,

                "VIOLENCE DETECTED"

            )

            sos_trigger.violence_detected(

                output,

                confidence,

                camera,

                location

            )

        #############################################
        # Recording
        #############################################

        if help_detected or violence_detected:

            if not self.recording:

                h, w = output.shape[:2]

                media_manager.start_recording(

                    w,

                    h,

                    20

                )

                self.recording = True

        if self.recording:

            media_manager.write(output)

        #############################################
        # Dashboard Overlay
        #############################################

        overlay(output)

        #############################################
        # FPS
        #############################################

        self.frame_counter += 1

        elapsed = max(

            time.time() - self.start_time,

            0.001

        )

        fps = self.frame_counter / elapsed

        #############################################
        # HUD
        #############################################

        cv2.putText(

            output,

            f"FPS : {fps:.1f}",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (0,255,0),

            2

        )

        cv2.putText(

            output,

            f"Persons : {person_count}",

            (20,75),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (255,255,0),

            2

        )

        cv2.putText(

            output,

            f"Vehicles : {vehicle_count}",

            (20,110),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (255,255,0),

            2

        )

        cv2.putText(

            output,

            f"Confidence : {confidence:.2f}",

            (20,145),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (255,255,255),

            2

        )

        return {

            "frame": output,

            "detections": detections,

            "persons": person_count,

            "vehicles": vehicle_count,

            "help": help_detected,

            "violence": violence_detected,

            "confidence": confidence,

            "fps": fps

        }

    def stop(self):

        if self.recording:

            media_manager.stop_recording()

            self.recording = False


pipeline = AIPipeline()