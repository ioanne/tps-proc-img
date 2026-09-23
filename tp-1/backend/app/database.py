from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, _record):
    """SQLite does not enforce FOREIGN KEY or ON DELETE unless enabled on every connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base for the ORM models (each team defines the models)."""


def get_db():
    """FastAPI dependency: opens one session per request and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Creates the tables for every model that inherits from `Base`.

    Important: the models must be imported before calling this function so
    that SQLAlchemy registers them in `Base.metadata`.
    """
    Base.metadata.create_all(bind=engine)
