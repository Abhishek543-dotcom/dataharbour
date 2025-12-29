"""
Cluster repository for database operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.repositories.base_repository import BaseRepository
from app.models.db_models import Cluster


class ClusterRepository(BaseRepository[Cluster]):
    """Repository for Cluster model operations"""

    def __init__(self):
        super().__init__(Cluster)

    def get_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Cluster]:
        """Get all clusters for a specific user"""
        return db.query(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, status: str, user_id: Optional[str] = None) -> List[Cluster]:
        """Get clusters by status"""
        query = db.query(self.model).filter(self.model.status == status)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.all()

    def get_running_clusters(self, db: Session, user_id: Optional[str] = None) -> List[Cluster]:
        """Get all running clusters"""
        return self.get_by_status(db, "running", user_id)

    def get_by_name(self, db: Session, name: str, user_id: Optional[str] = None) -> Optional[Cluster]:
        """Get cluster by name"""
        query = db.query(self.model).filter(self.model.name == name)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.first()

    def count_by_status(self, db: Session, status: str, user_id: Optional[str] = None) -> int:
        """Count clusters by status"""
        query = db.query(self.model).filter(self.model.status == status)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.count()
