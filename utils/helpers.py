import cv2
import os
import time
from pathlib import Path
from datetime import datetime


def timestamp():

    return datetime.now().strftime(

        "%Y-%m-%d %H:%M:%S"

    )


def filename(prefix="capture", extension="jpg"):

    return f"{prefix}_{int(time.time())}.{extension}"


def ensure_directory(path):

    Path(path).mkdir(

        parents=True,

        exist_ok=True

    )


def save_image(frame, directory):

    ensure_directory(directory)

    path = os.path.join(

        directory,

        filename("alert")

    )

    cv2.imwrite(path, frame)

    return path


def resize(frame, width=1280):

    h, w = frame.shape[:2]

    ratio = width / w

    height = int(h * ratio)

    return cv2.resize(

        frame,

        (width, height)

    )


def draw_text(

    frame,

    text,

    position,

    color=(0,255,0)

):

    cv2.putText(

        frame,

        text,

        position,

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        color,

        2

    )


def draw_box(

    frame,

    x1,

    y1,

    x2,

    y2,

    label,

    color=(0,255,0)

):

    cv2.rectangle(

        frame,

        (x1, y1),

        (x2, y2),

        color,

        2

    )

    cv2.putText(

        frame,

        label,

        (x1, y1 - 8),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        color,

        2

    )


def current_time():

    return datetime.now().strftime(

        "%H:%M:%S"

    )


def fps(start, frames):

    elapsed = time.time() - start

    if elapsed == 0:

        return 0

    return round(

        frames / elapsed,

        2

    )


def overlay(frame):

    cv2.putText(

        frame,

        timestamp(),

        (20, frame.shape[0] - 20),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255,255,255),

        2

    )

    return frame


def success(message):

    print(

        f"[SUCCESS] {message}"

    )


def warning(message):

    print(

        f"[WARNING] {message}"

    )


def error(message):

    print(

        f"[ERROR] {message}"

    )


def info(message):

    print(

        f"[INFO] {message}"

    )


def draw_banner(

    frame,

    text,

    color=(0,0,255)

):

    cv2.rectangle(

        frame,

        (0,0),

        (frame.shape[1],60),

        color,

        -1

    )

    cv2.putText(

        frame,

        text,

        (20,40),

        cv2.FONT_HERSHEY_SIMPLEX,

        1,

        (255,255,255),

        2

    )

    return frame


def percentage(value):

    return f"{round(value,2)}%"


def center(frame):

    h, w = frame.shape[:2]

    return (

        w // 2,

        h // 2

    )


def distance(p1, p2):

    return (

        (p1[0]-p2[0])**2 +

        (p1[1]-p2[1])**2

    ) ** 0.5