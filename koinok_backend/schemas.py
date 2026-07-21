"""
schemas.py
----------
Pydantic v2 request/response validation schemas.

Milestone 1 schemas:
  - UserRegister   — registration body
  - UserLogin      — login body
  - UserResponse   — safe user projection returned to clients
  - Token          — JWT token envelope
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
