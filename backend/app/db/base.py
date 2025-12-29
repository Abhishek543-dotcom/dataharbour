"""
SQLAlchemy Base class for all database models
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here so Alembic can detect them
from app.models.db_models import User, Job, Notebook, Cluster, UserSettings, APIKey  # noqa
