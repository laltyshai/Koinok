"""
security.py
-----------
All cryptographic and authentication logic lives HERE, strictly isolated.

When you migrate to Firebase Auth:
  1. Delete `CryptContext`, `hash_password`, `verify_password`, `create_access_token`.
  2. Replace the body of `get_current_user` with Firebase token verification.
  3. Nothing else in the codebase needs to change.

Contents:
  - Password hashing utilities (bcrypt via passlib)
  - JWT creation / decoding (python-jose)
  - `get_current_user` FastAPI dependency
"""

import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db

# ---------------------------------------------------------------------------
# JWT constants — override SECRET_KEY via environment variable in production
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-before-deploying-to-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return the bcrypt hash of a plain-text password."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches its stored hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT token management
# ---------------------------------------------------------------------------
def create_access_token(data: dict) -> str:
    """
    Sign and return a JWT token.

    Args:
        data: Payload to encode (typically {"sub": user_email}).

    Returns:
        Compact JWS string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# OAuth2 scheme — advertises the login URL to Swagger UI
# ---------------------------------------------------------------------------
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------------------------------------------------------
# Dependency: get_current_user
# ---------------------------------------------------------------------------
def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency that decodes the incoming Bearer token and returns
    the corresponding `UserModel` from the database.

    Raises:
        HTTPException 401: If the token is invalid, expired, or the user
                           no longer exists.
    """
    # Import here to avoid circular imports at module load time
    from db_models import UserModel

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user is None:
        raise credentials_exception

    return user
