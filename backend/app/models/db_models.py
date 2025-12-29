"""
SQLAlchemy ORM models for DataHarbour database tables
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    notebooks = relationship("Notebook", back_populates="user", cascade="all, delete-orphan")
    clusters = relationship("Cluster", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class Job(Base):
    """Job model for Spark job tracking"""
    __tablename__ = "jobs"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # pending, running, completed, failed
    cluster = Column(String(100), nullable=False)
    code = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    config = Column(JSONB, default={}, nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=True)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    duration = Column(String(50), nullable=True)
    spark_ui_url = Column(String(500), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="jobs")

    # Indexes for better query performance
    __table_args__ = (
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_user_id", "user_id"),
        Index("idx_jobs_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Job(id={self.id}, name={self.name}, status={self.status})>"


class Notebook(Base):
    """Notebook model for Jupyter-style notebooks"""
    __tablename__ = "notebooks"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cells = Column(JSONB, default=[], nullable=False)  # Array of cell objects
    path = Column(String(500), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notebooks")

    # Indexes
    __table_args__ = (
        Index("idx_notebooks_user_id", "user_id"),
        Index("idx_notebooks_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Notebook(id={self.id}, name={self.name})>"


class Cluster(Base):
    """Cluster model for Spark cluster management"""
    __tablename__ = "clusters"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # running, stopped, error
    master_url = Column(String(500), nullable=False)
    ui_url = Column(String(500), nullable=True)
    worker_nodes = Column(Integer, default=2, nullable=False)
    total_cores = Column(Integer, default=4, nullable=False)
    total_memory = Column(String(20), default="4g", nullable=False)
    config = Column(JSONB, default={}, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="clusters")

    # Indexes
    __table_args__ = (
        Index("idx_clusters_user_id", "user_id"),
        Index("idx_clusters_status", "status"),
    )

    def __repr__(self):
        return f"<Cluster(id={self.id}, name={self.name}, status={self.status})>"


class UserSettings(Base):
    """User settings and preferences"""
    __tablename__ = "user_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme = Column(String(20), default="light", nullable=False)  # light, dark, system
    preferences = Column(JSONB, default={}, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, theme={self.theme})>"


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)  # Hashed API key for security
    last_used = Column(TIMESTAMP(timezone=True), nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    # Indexes
    __table_args__ = (
        Index("idx_api_keys_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<APIKey(id={self.id}, key_name={self.key_name})>"
