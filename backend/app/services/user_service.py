"""
User service for authentication and user management
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.db.repositories.user_repository import UserRepository
from app.core.config import settings
from app.models.schemas import UserCreate, UserUpdate, User

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError as e:
            logger.error(f"JWT Error: {e}")
            return None

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = self.repository.get_by_email(db, user_data.email)
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")

        existing_username = self.repository.get_by_username(db, user_data.username)
        if existing_username:
            raise ValueError(f"Username {user_data.username} already taken")

        # Hash password
        hashed_password = self._hash_password(user_data.password)

        # Create user dict
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_superuser": False
        }

        # Create in database
        user_db = self.repository.create(db, user_dict)
        logger.info(f"User {user_data.username} created successfully")

        return User.model_validate(user_db)

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user_db = self.repository.get_by_email(db, email)
        if not user_db:
            return None

        if not self._verify_password(password, user_db.hashed_password):
            return None

        if not user_db.is_active:
            logger.warning(f"Inactive user attempted login: {email}")
            return None

        return User.model_validate(user_db)

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_db = self.repository.get_by_id(db, user_id)
        if user_db:
            return User.model_validate(user_db)
        return None

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        user_db = self.repository.get_by_email(db, email)
        if user_db:
            return User.model_validate(user_db)
        return None

    def update_user(self, db: Session, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        update_dict = {}

        if user_data.email:
            # Check if email is already taken by another user
            existing_user = self.repository.get_by_email(db, user_data.email)
            if existing_user and str(existing_user.id) != user_id:
                raise ValueError(f"Email {user_data.email} already in use")
            update_dict["email"] = user_data.email

        if user_data.username:
            # Check if username is already taken by another user
            existing_user = self.repository.get_by_username(db, user_data.username)
            if existing_user and str(existing_user.id) != user_id:
                raise ValueError(f"Username {user_data.username} already taken")
            update_dict["username"] = user_data.username

        if user_data.full_name is not None:
            update_dict["full_name"] = user_data.full_name

        if user_data.password:
            update_dict["hashed_password"] = self._hash_password(user_data.password)

        if update_dict:
            updated_user = self.repository.update(db, user_id, update_dict)
            if updated_user:
                return User.model_validate(updated_user)

        return None

    def deactivate_user(self, db: Session, user_id: str) -> bool:
        """Deactivate a user account"""
        user = self.repository.deactivate_user(db, user_id)
        return user is not None

    def activate_user(self, db: Session, user_id: str) -> bool:
        """Activate a user account"""
        user = self.repository.activate_user(db, user_id)
        return user is not None


# Singleton instance
user_service = UserService()
