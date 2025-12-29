"""
Settings repository for database operations
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.repositories.base_repository import BaseRepository
from app.models.db_models import UserSettings


class SettingsRepository(BaseRepository[UserSettings]):
    """Repository for UserSettings model operations"""

    def __init__(self):
        super().__init__(UserSettings)

    def get_by_user_id(self, db: Session, user_id: str) -> Optional[UserSettings]:
        """Get settings for a specific user"""
        return db.query(self.model).filter(self.model.user_id == user_id).first()

    def create_default_settings(self, db: Session, user_id: str) -> UserSettings:
        """Create default settings for a new user"""
        settings = self.model(
            user_id=user_id,
            theme="light",
            preferences={}
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    def update_theme(self, db: Session, user_id: str, theme: str) -> Optional[UserSettings]:
        """Update user's theme preference"""
        settings = self.get_by_user_id(db, user_id)
        if settings:
            settings.theme = theme
            db.commit()
            db.refresh(settings)
        return settings

    def update_preferences(self, db: Session, user_id: str, preferences: Dict[str, Any]) -> Optional[UserSettings]:
        """Update user's preferences"""
        settings = self.get_by_user_id(db, user_id)
        if settings:
            # Merge new preferences with existing ones
            current_prefs = settings.preferences or {}
            current_prefs.update(preferences)
            settings.preferences = current_prefs
            db.commit()
            db.refresh(settings)
        return settings

    def get_or_create(self, db: Session, user_id: str) -> UserSettings:
        """Get settings or create default if not exists"""
        settings = self.get_by_user_id(db, user_id)
        if not settings:
            settings = self.create_default_settings(db, user_id)
        return settings
