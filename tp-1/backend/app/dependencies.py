"""FastAPI dependencies: build the core objects for each request."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.imaging import ImageCodec
from app.core.service import ImageService
from app.core.storage import FileStorage
from app.dal import ImageDAL
from app.database import get_db


def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    return ImageService(ImageDAL(db), FileStorage(), ImageCodec())
