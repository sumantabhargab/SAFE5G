import cv2
from pathlib import Path
from datetime import datetime

from utils.config import IMAGE_PATH, VIDEO_PATH


class MediaManager:

    def __init__(self):

        self.video_writer = None

        self.recording = False

        self.video_file = None

    def timestamp(self):

        return datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )

    def image_name(self):

        return IMAGE_PATH / f"img_{self.timestamp()}.jpg"

    def video_name(self):

        return VIDEO_PATH / f"video_{self.timestamp()}.mp4"

    def save_frame(self, frame):

        IMAGE_PATH.mkdir(

            parents=True,

            exist_ok=True

        )

        path = self.image_name()

        cv2.imwrite(

            str(path),

            frame

        )

        return str(path)

    def start_recording(

        self,

        width,

        height,

        fps=20

    ):

        if self.recording:

            return

        VIDEO_PATH.mkdir(

            parents=True,

            exist_ok=True

        )

        self.video_file = self.video_name()

        fourcc = cv2.VideoWriter_fourcc(

            *"mp4v"

        )

        self.video_writer = cv2.VideoWriter(

            str(self.video_file),

            fourcc,

            fps,

            (width, height)

        )

        self.recording = True

    def write(self, frame):

        if self.recording and self.video_writer:

            self.video_writer.write(

                frame

            )

    def stop_recording(self):

        if self.video_writer:

            self.video_writer.release()

            self.video_writer = None

        self.recording = False

        return str(self.video_file)

    def snapshot(

        self,

        frame,

        label="Alert"

    ):

        frame = frame.copy()

        cv2.putText(

            frame,

            label,

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0, 0, 255),

            2

        )

        return self.save_frame(frame)

    def save_clip(

        self,

        frames,

        fps=20

    ):

        if not frames:

            return None

        h, w = frames[0].shape[:2]

        self.start_recording(

            w,

            h,

            fps

        )

        for frame in frames:

            self.write(frame)

        return self.stop_recording()

    def release(self):

        self.stop_recording()

    def is_recording(self):

        return self.recording


media_manager = MediaManager()