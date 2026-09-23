"""
Acceptance test configuration. DO NOT MODIFY.

Redirects the database and the image folder to a temporary directory
BEFORE importing the application, so the tests do not touch the real data.
"""

import os
import shutil
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="tp1-tests-"))
STORAGE_DIR = _TMP / "images"
DB_PATH = _TMP / "test.db"
os.environ["TP_STORAGE_DIR"] = str(STORAGE_DIR)
os.environ["TP_DATABASE_URL"] = f"sqlite:///{DB_PATH}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP, ignore_errors=True)
