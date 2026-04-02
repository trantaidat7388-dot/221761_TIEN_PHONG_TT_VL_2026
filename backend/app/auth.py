# auth.py - JWT + bcrypt authentication helpers

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# ── CONFIG ──────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
PREVIOUS_SECRET_KEYS = [
    key.strip() for key in os.getenv("JWT_PREVIOUS_SECRET_KEYS", "").split(",") if key.strip()
]

if not SECRET_KEY:
    if APP_ENV in {"production", "prod"}:
        raise RuntimeError("JWT_SECRET_KEY is required in production environment")
    SECRET_KEY = "dev-only-change-me-before-deploy"
    logger.warning(
        "JWT_SECRET_KEY is not set. Using insecure development fallback key. "
        "Set JWT_SECRET_KEY in environment before deploying."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # 7 ngày

# ── PASSWORD HASHING ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── JWT ───────────────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _decode_with_rotated_keys(token: str) -> dict:
    """Try current key first, then previous keys to support key rotation."""
    secrets_to_try = [SECRET_KEY, *PREVIOUS_SECRET_KEYS]
    for secret in secrets_to_try:
        try:
            return jwt.decode(token, secret, algorithms=[ALGORITHM])
        except JWTError:
            continue
    raise JWTError("Token signature validation failed for all configured keys")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = _decode_with_rotated_keys(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
