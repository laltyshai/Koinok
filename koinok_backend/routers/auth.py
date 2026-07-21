"""
routers/auth.py
---------------
Authentication endpoints.

Isolation contract:
  - Password hashing  → security.py
  - Token generation  → security.py
  - DB session        → database.get_db()
  - Models            → db_models.py
  - Schemas           → schemas.py

When migrating to Firebase Auth, swap this file's register/login logic
for Firebase Admin SDK calls — nothing outside this file changes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import UserModel
from schemas import Token, UserLogin, UserRegister, UserResponse
from security import create_access_token, hash_password, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(body: UserRegister, db: Session = Depends(get_db)):
    """
    Create a new user profile.

    - Rejects duplicate email addresses with **400**.
    - Stores only the bcrypt hash of the password — never the plain text.
    """
    # Guard: duplicate email
    existing = db.query(UserModel).filter(UserModel.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = UserModel(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT access token",
)
def login(body: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate with email + password.

    Returns a signed **JWT Bearer token** on success.
    Raises **401** for any credential mismatch (deliberately vague for security).
    """
    user = db.query(UserModel).filter(UserModel.email == body.email).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token)
