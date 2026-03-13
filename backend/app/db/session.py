"""
Database session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from app.core.config import settings

kwargs = {
    "pool_pre_ping": True,  # Verify connections before using
    "echo": settings.ENVIRONMENT == "development",  # Log SQL queries in development
}
if not settings.DATABASE_URL.startswith("sqlite"):
    kwargs["pool_size"] = 5
    kwargs["max_overflow"] = 10

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    **kwargs
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator:
    """
    Dependency function to get database session.
    Usage in FastAPI endpoints:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
