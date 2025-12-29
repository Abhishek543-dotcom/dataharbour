"""
Notebook repository for database operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.repositories.base_repository import BaseRepository
from app.models.db_models import Notebook


class NotebookRepository(BaseRepository[Notebook]):
    """Repository for Notebook model operations"""

    def __init__(self):
        super().__init__(Notebook)

    def get_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Notebook]:
        """Get all notebooks for a specific user"""
        return db.query(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit).all()

    def get_recent_notebooks(self, db: Session, user_id: Optional[str] = None, limit: int = 10) -> List[Notebook]:
        """Get recent notebooks ordered by update date"""
        query = db.query(self.model)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.order_by(self.model.updated_at.desc()).limit(limit).all()

    def search_notebooks(self, db: Session, search_term: str, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Notebook]:
        """Search notebooks by name or description"""
        query = db.query(self.model).filter(
            (self.model.name.ilike(f"%{search_term}%")) |
            (self.model.description.ilike(f"%{search_term}%"))
        )
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        return query.offset(skip).limit(limit).all()

    def count_by_user(self, db: Session, user_id: str) -> int:
        """Count notebooks for a specific user"""
        return db.query(self.model).filter(self.model.user_id == user_id).count()
