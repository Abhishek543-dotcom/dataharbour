import secrets
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

# JWT Token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    """Verify and decode a JWT access token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise credentials_exception

# API Key validation
def validate_api_key(api_key: str) -> bool:
    """Validate an API key (placeholder - implement with database)"""
    # TODO: Implement API key validation with database
    # For now, compare with a configured key
    valid_key = settings.API_KEY if hasattr(settings, 'API_KEY') else None
    if valid_key is None:
        return False
    return secrets.compare_digest(api_key, valid_key)

# Input sanitization
def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not value:
        return value

    # Trim to max length
    value = value[:max_length]

    # Remove null bytes
    value = value.replace('\x00', '')

    # Remove potentially dangerous characters for code execution
    # Note: This is basic sanitization. For code execution, use sandboxing
    dangerous_patterns = ['__import__', 'eval(', 'exec(', 'compile(', 'open(']
    for pattern in dangerous_patterns:
        if pattern in value.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input contains potentially dangerous pattern: {pattern}"
            )

    return value

def validate_notebook_name(name: str) -> str:
    """Validate notebook name"""
    if not name or len(name) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notebook name cannot be empty"
        )

    if len(name) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notebook name too long (max 255 characters)"
        )

    # Only allow alphanumeric, spaces, hyphens, underscores
    import re
    if not re.match(r'^[\w\s\-]+$', name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notebook name contains invalid characters"
        )

    return name

def validate_job_name(name: str) -> str:
    """Validate job name"""
    if not name or len(name) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job name cannot be empty"
        )

    if len(name) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job name too long (max 255 characters)"
        )

    return name

def validate_code_length(code: str, max_length: int = 100000) -> str:
    """Validate code length"""
    if len(code) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code too long (max {max_length} characters)"
        )

    return code
