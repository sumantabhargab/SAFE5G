from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


MODEL_DIR = BASE_DIR / "models"

MEDIA_DIR = BASE_DIR / "media"

DATABASE = BASE_DIR / "safe5g.db"


YOLO_MODEL = MODEL_DIR / "yolov8n.pt"

GESTURE_MODEL = MODEL_DIR / "gesture.onnx"

VIOLENCE_MODEL = MODEL_DIR / "violence.keras"


CAMERA_INDEX = 0

FRAME_WIDTH = 1280

FRAME_HEIGHT = 720

FPS = 30


YOLO_CONFIDENCE = 0.40

VIOLENCE_THRESHOLD = 0.70

GESTURE_THRESHOLD = 0.80


SAVE_IMAGES = True

SAVE_VIDEO = True

SAVE_LOGS = True

SAVE_REPORTS = True


IMAGE_PATH = MEDIA_DIR / "images"

VIDEO_PATH = MEDIA_DIR / "videos"

REPORT_PATH = MEDIA_DIR / "reports"

LOG_PATH = MEDIA_DIR / "logs"


for directory in [

    MODEL_DIR,

    MEDIA_DIR,

    IMAGE_PATH,

    VIDEO_PATH,

    REPORT_PATH,

    LOG_PATH

]:

    directory.mkdir(

        parents=True,

        exist_ok=True

    )


CAMERAS = {

    1: {

        "name": "Front Gate",

        "source": 0

    },

    2: {

        "name": "Parking",

        "source": 1

    },

    3: {

        "name": "Lobby",

        "source": 2

    },

    4: {

        "name": "Corridor",

        "source": 3

    }

}


COLORS = {

    "danger": (0, 0, 255),

    "warning": (0, 165, 255),

    "safe": (0, 255, 0),

    "info": (255, 255, 0)

}


ALERT_TYPES = [

    "Violence",

    "HELP Gesture",

    "Unknown Person",

    "Crowd",

    "Intrusion",

    "Fall Detection",

    "Suspicious Object"

]


SYSTEM_NAME = "Safe5G"

VERSION = "1.0"

AUTHOR = "Sumanta Bhargab"
