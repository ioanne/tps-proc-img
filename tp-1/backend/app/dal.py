"""
Data access layer: every SQL query of the application lives here.

The rest of the code (core and routers) never builds queries: it asks an
`ImageDAL` for what it needs.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ImageRecord


class ImageDAL:
    """CRUD over the `images` table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **fields: Any) -> ImageRecord:
        record = ImageRecord(**fields)
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get(self, image_id: int) -> ImageRecord | None:
        return self._session.get(ImageRecord, image_id)

    def list(self) -> list[ImageRecord]:
        """All the images, newest first (descending id)."""
        return list(self._session.scalars(select(ImageRecord).order_by(ImageRecord.id.desc())))

    def update(self, record: ImageRecord, **fields: Any) -> ImageRecord:
        for name, value in fields.items():
            setattr(record, name, value)
        self._session.commit()
        self._session.refresh(record)
        return record

    def delete(self, record: ImageRecord) -> None:
        """Deletes the row. The database sets `source_id = NULL` in the derived images."""
        self._session.delete(record)
        self._session.commit()
