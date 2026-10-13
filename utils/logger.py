import logging
import os
from pathlib import Path
from utils.config import LOG_PATH


logger = logging.getLogger("Safe5G")
logger.setLevel(logging.DEBUG)

# File handler
LOG_PATH.mkdir(parents=True, exist_ok=True)
handler = logging.FileHandler(LOG_PATH / "safe5g.log")
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))
logger.addHandler(handler)

# Console handler
console = logging.StreamHandler()
console.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger.addHandler(console)
