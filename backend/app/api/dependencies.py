"""
API dependencies for authentication and authorization
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.user_service import user_service
from app.models.schemas import User
from app.core.config import settings

# Security schemes
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    # If auth is disabled (for development), return None or skip validation
    if not settings.ENABLE_AUTH:
        return None

    token = credentials.credentials

    # Verify token and get user_id
    user_id = user_service.verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is active
    """
    if current_user and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is a superuser (admin)
    """
    if current_user and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[User]:
    """
    Dependency to optionally get current user (doesn't fail if not authenticated)
    Useful for endpoints that work with or without authentication
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user_id = user_service.verify_token(token)
        if user_id:
            return user_service.get_user_by_id(db, user_id)
    except:
        pass

    return None
