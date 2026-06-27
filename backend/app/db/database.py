from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
else:
    engine = None

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine if engine is not None else None,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """FastAPI dependency — request ke end pe session auto-close."""
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured")
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """
    Development mein use karo. Production mein Alembic migrations use karo.
    """
    from app.models import Base
    Base.metadata.create_all(bind=engine)