import cv2
import config

from camera.webcam import Webcam
from ai.tracker import Tracker
from ai.violence_detector import ViolenceDetector


def main():

    print("=" * 50)
    print("Starting Safe5G...")
    print("=" * 50)

    # ----------------------------------------
    # Initialize
    # ----------------------------------------

    camera = Webcam()
    tracker = Tracker()

    violence_detector = ViolenceDetector(
        config.VIOLENCE_MODEL
    )

    camera.start()

    frame_count = 0

    violence_probability = 0.0
    violence_label = "Unknown"

    # ----------------------------------------

    while True:

        frame = camera.read()

        if frame is None:
            break

        # ------------------------------------
        # Person Tracking
        # ------------------------------------

        tracked_people = tracker.update(frame)

        annotated = frame.copy()

        for person in tracked_people:

            x1, y1, x2, y2 = person.bbox

            cv2.rectangle(

                annotated,

                (x1, y1),

                (x2, y2),

                (0,255,0),

                2

            )

            cv2.putText(

                annotated,

                f"ID : {person.id}",

                (x1,y1-10),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (0,255,0),

                2

            )

        # ------------------------------------
        # Violence Detection
        # ------------------------------------

        if frame_count % config.FRAME_SKIP_FOR_VIOLENCE == 0:

            result = violence_detector.predict(frame)

            violence_probability = result["violence_probability"]

            violence_label = result["label"]

        frame_count += 1

        # ------------------------------------
        # Decide Threat Level
        # ------------------------------------

        if violence_probability > 0.90:

            threat = "CRITICAL"
            color = (0,0,255)

        elif violence_probability > 0.75:

            threat = "HIGH"
            color = (0,69,255)

        elif violence_probability > 0.50:

            threat = "MEDIUM"
            color = (0,165,255)

        else:

            threat = "SAFE"
            color = (0,255,0)

        # ------------------------------------
        # Draw Information
        # ------------------------------------

        cv2.putText(

            annotated,

            f"People : {len(tracked_people)}",

            (20,40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255,255,255),

            2

        )

        cv2.putText(

            annotated,

            f"Violence : {violence_label}",

            (20,80),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            color,

            2

        )

        cv2.putText(

            annotated,

            f"Probability : {violence_probability:.2f}",

            (20,120),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            color,

            2

        )

        cv2.putText(

            annotated,

            f"Threat : {threat}",

            (20,160),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.9,

            color,

            3

        )

        cv2.imshow(

            config.WINDOW_NAME,

            annotated

        )

        key = cv2.waitKey(1)

        if key == ord("q"):

            break

    camera.stop()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    main()