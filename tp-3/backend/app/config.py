"""
Application settings. DO NOT MODIFY.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Accepted photo formats (detected by content, not by extension).
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP", "BMP"}

# Maximum size of an uploaded photo.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# Images bigger than this are sent shrunk in the step previews of /api/avatar/steps.
PREVIEW_SIDE = 512
