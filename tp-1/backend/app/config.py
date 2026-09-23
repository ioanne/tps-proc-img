"""
Application configuration.

The core and the routers MUST use these constants (not hand-written paths):
the acceptance tests redirect them to temporary folders through environment
variables.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Folder where the image files are stored (originals and results).
STORAGE_DIR = Path(os.environ.get("TP_STORAGE_DIR", BASE_DIR / "storage" / "images"))

# Public prefix under which the files in STORAGE_DIR are served.
# An image stored as STORAGE_DIR / "abc.png" is accessed at MEDIA_URL + "/abc.png".
MEDIA_URL = "/media"

# SQLite database.
DATABASE_URL = os.environ.get("TP_DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'app.db'}")

# Frontend folder (served at "/").
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Accepted formats, using the names Pillow uses in `Image.format`.
# The format is determined by the file CONTENT, not by its extension or its content-type.
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP", "BMP"}

# Maximum uploaded file size.
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
