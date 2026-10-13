from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "ai" / "models"

MEDIA_DIR = BASE_DIR / "media"

DATABASE = BASE_DIR / "safe5g.db"


YOLO_MODEL = MODEL_DIR / "yolov8n.pt"

VIOLENCE_MODEL = MODEL_DIR / "violence_classifier.pth"

HEADLESS = os.getenv("SAFE5G_HEADLESS", "0").lower() == "1"


CAMERA_INDEX = 2

FRAME_WIDTH = 640

FRAME_HEIGHT = 480

FPS = 15


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

# ReID tracking — stable person IDs across frames
TRACKER_ENABLED = True
TRACKER_MAX_AGE = 30
TRACKER_N_INIT = 3
TRACKER_MAX_COSINE_DIST = 0.5


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

# SOS escalation — loaded from .env via load_dotenv()
SOS_WEBHOOK = os.getenv("SOS_WEBHOOK", "")
SOS_PHONE = os.getenv("SOS_PHONE", "")
SOS_EMAIL = os.getenv("SOS_EMAIL", "")
