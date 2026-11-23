"""
Modular Authentication Service for GroceryPi.

Provides bcrypt password hashing, JWT token creation, and conditional request
verification:
- Local Raspberry Pi kiosk requests (from localhost / 127.0.0.1) stay zero-friction
  and hands-free without requiring a password.
- Remote mobile/web browser requests require a valid signed JWT token unlocked
  with a bcrypt-hashed password.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)


class AuthService:
    """Handles password hashing, token creation, and local-kiosk vs remote-mobile access checks."""

    LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a plain-text password with bcrypt."""
        return hash_password(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Checks a plain-text password against a saved bcrypt hash."""
        return verify_password(plain, hashed)

    @staticmethod
    def create_token(user_id: int, expires_minutes: Optional[int] = None) -> str:
        """Creates a signed JWT token for an authenticated user."""
        delta = timedelta(minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(data={"sub": str(user_id)}, expires_delta=delta)

    @classmethod
    def is_local_kiosk_request(cls, request: Request) -> bool:
        """
        Returns True if the request comes directly from the local Raspberry Pi
        touchscreen kiosk (localhost / 127.0.0.1), allowing hands-free operation.
        """
        client_host = (request.client.host if request.client else "").strip().lower()
        force_remote = request.headers.get("X-GroceryPi-Remote-Mobile", "").lower() == "true"
        if force_remote:
            return False
        return client_host in cls.LOCAL_HOSTS


auth_service = AuthService()
