"""
User repository for database operations
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.db.repositories.base_repository import BaseRepository
from app.models.db_models import User


class UserRepository(BaseRepository[User]):
    """Repository for User model operations"""

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(self.model).filter(self.model.email == email).first()

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(self.model).filter(self.model.username == username).first()

    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100):
        """Get all active users"""
        return db.query(self.model).filter(self.model.is_active == True).offset(skip).limit(limit).all()

    def get_superusers(self, db: Session):
        """Get all superuser accounts"""
        return db.query(self.model).filter(self.model.is_superuser == True).all()

    def deactivate_user(self, db: Session, user_id: str) -> Optional[User]:
        """Deactivate a user account"""
        return self.update(db, user_id, {"is_active": False})

    def activate_user(self, db: Session, user_id: str) -> Optional[User]:
        """Activate a user account"""
        return self.update(db, user_id, {"is_active": True})
