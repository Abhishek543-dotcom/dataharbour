"""
Job repository for database operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.repositories.base_repository import BaseRepository
from app.models.db_models import Job


class JobRepository(BaseRepository[Job]):
    """Repository for Job model operations"""

    def __init__(self):
        super().__init__(Job)

    def get_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get all jobs for a specific user"""
        return db.query(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, status: str, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get jobs by status"""
        query = db.query(self.model).filter(self.model.status == status)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.offset(skip).limit(limit).all()

    def get_by_cluster(self, db: Session, cluster: str, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get jobs by cluster"""
        query = db.query(self.model).filter(self.model.cluster == cluster)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.offset(skip).limit(limit).all()

    def get_running_jobs(self, db: Session, user_id: Optional[str] = None) -> List[Job]:
        """Get all running jobs, optionally filtered by user"""
        query = db.query(self.model).filter(self.model.status == "running")
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.all()

    def get_recent_jobs(self, db: Session, user_id: Optional[str] = None, limit: int = 10) -> List[Job]:
        """Get recent jobs ordered by creation date"""
        query = db.query(self.model)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.order_by(self.model.created_at.desc()).limit(limit).all()

    def count_by_status(self, db: Session, status: str, user_id: Optional[str] = None) -> int:
        """Count jobs by status"""
        query = db.query(self.model).filter(self.model.status == status)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.count()

    def search_jobs(self, db: Session, search_term: str, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Job]:
        """Search jobs by name"""
        query = db.query(self.model).filter(self.model.name.ilike(f"%{search_term}%"))
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.offset(skip).limit(limit).all()
