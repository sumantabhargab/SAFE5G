from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "ai" / "models"

MEDIA_DIR = BASE_DIR / "media"

DATABASE = BASE_DIR / "safe5g.db"


YOLO_MODEL = MODEL_DIR / "yolov8n.pt"

VIOLENCE_MODEL = MODEL_DIR / "violence_classifier.pth"

GESTURE_MODEL = MODEL_DIR / "gesture.onnx"


CAMERA_INDEX = 0

FRAME_WIDTH = 1280

FRAME_HEIGHT = 720

FPS = 30


YOLO_CONFIDENCE = 0.40

VIOLENCE_THRESHOLD = 0.70

GESTURE_THRESHOLD = 0.80


# Violence window voting: N-frame window, positive if >= VOTES frames violent
VIOLENCE_WINDOW = 16

VIOLENCE_WINDOW_VOTES = 8

# Gesture temporal confirmation: consecutive frames required
GESTURE_CONFIRM_FRAMES = 5


# Alert cooldown per type per camera (seconds)
ALERT_COOLDOWN = 60


SAVE_IMAGES = True

SAVE_VIDEO = True

SAVE_LOGS = True

SAVE_REPORTS = True


IMAGE_PATH = MEDIA_DIR / "images"

VIDEO_PATH = MEDIA_DIR / "videos"

REPORT_PATH = MEDIA_DIR / "reports"

LOG_PATH = MEDIA_DIR / "logs"


for directory in [MODEL_DIR, MEDIA_DIR, IMAGE_PATH, VIDEO_PATH, REPORT_PATH, LOG_PATH]:

    directory.mkdir(parents=True, exist_ok=True)


CAMERAS = {

    1: {

        "name": "Camera 01",

        "location": "Main Gate",

        "source": 0

    }

}


# Single source of truth for drawing colors (BGR)
GREEN = (0, 255, 0)

RED = (0, 0, 255)

YELLOW = (0, 255, 255)

ORANGE = (0, 165, 255)

BLUE = (255, 255, 0)

WHITE = (255, 255, 255)


COLORS = {

    "danger": RED,

    "warning": ORANGE,

    "safe": GREEN,

    "info": BLUE

}


# Threat level -> color (used by pipeline HUD and overlays)
THREAT_COLORS = {

    "SAFE": GREEN,

    "LOW": YELLOW,

    "MEDIUM": ORANGE,

    "HIGH": RED,

    "CRITICAL": RED

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

VERSION = "1.1"

AUTHOR = "Sumanta Bhargab"
