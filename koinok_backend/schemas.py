"""
schemas.py
----------
Pydantic v2 request/response validation schemas.

Milestone 1 schemas:
  - UserRegister   — registration body
  - UserLogin      — login body
  - UserResponse   — safe user projection returned to clients
  - Token          — JWT token envelope

Milestone 2 schemas:
  - ClothCategory  — category enum
  - ClothBase      — shared cloth fields
  - ClothCreate    — cloth creation payload
  - ClothUpdate    — partial update payload
  - ClothResponse  — full cloth response schema
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


# ---------------------------------------------------------------------------
# Wardrobe schemas (Milestone 2)
# ---------------------------------------------------------------------------
class ClothCategory(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    FULLBODY = "fullbody"
    FOOTWEAR = "footwear"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"
    OTHER = "other"


class ClothBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: ClothCategory = Field(default=ClothCategory.OTHER)


class ClothCreate(ClothBase):
    pass


class ClothUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[ClothCategory] = None


class ClothResponse(ClothBase):
    id: int
    user_id: int
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)