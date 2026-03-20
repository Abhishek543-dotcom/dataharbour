"""
Authentication Routes
=====================
POST /auth/login   — Login (returns demo token; replace with JWT in production)
POST /auth/logout  — Logout
"""

import logging
from fastapi import APIRouter

from api.helpers import LoginRequest

logger = logging.getLogger("dataharbour.routes.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(credentials: LoginRequest):
    """
    Authenticate a user.

    **Note:** This is a stub implementation. In production, replace with
    JWT/OAuth2 token-based authentication.
    """
    logger.info("Login attempt for user: %s", credentials.username)
    return {
        "success": True,
        "user": {
            "username": credentials.username,
            "name": "DataHarbour User",
            "token": "demo-token-12345",
        },
    }


@router.post("/logout")
def logout():
    """Invalidate the current session."""
    return {"success": True, "message": "Logged out successfully"}

