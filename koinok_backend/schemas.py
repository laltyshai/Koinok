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













Milestone 3 schemas:
  - WearLogBase               — shared wear log fields
  - BatchLogCreate            — batch daily wear log payload
  - WearLogResponse           — wear log response schema
  - CalendarDayResponse       — single-day calendar entry
  - RotationSuggestionsResponse — 14-day rotation dashboard

Milestone 5 schemas:
  - ClothMatchRequest — bidirectional matchmaking request payload
  - ClothMatchItem    — simplified cloth projection nested inside ClothResponse.matching_clothes
  - LookCreate         — Look creation payload
  - LookResponse       — Look response schema with nested clothing items
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

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
    color: Optional[str] = Field(default=None, max_length=50)
    season: Optional[str] = Field(default=None, max_length=50)
    is_oversize: Optional[bool] = Field(default=False)


class ClothCreate(ClothBase):
    pass


class ClothUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[ClothCategory] = None
    color: Optional[str] = Field(default=None, max_length=50)
    season: Optional[str] = Field(default=None, max_length=50)
    is_oversize: Optional[bool] = None


class ClothMatchItem(BaseModel):
    """Simplified cloth projection used inside ClothResponse.matching_clothes — no
    nested matching_clothes of its own, so it can't recurse."""
    id: int
    name: str
    category: ClothCategory
    color: Optional[str] = None
    season: Optional[str] = None
    is_oversize: Optional[bool] = None
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClothResponse(ClothBase):
    id: int
    user_id: int
    is_deleted: bool
    created_at: datetime
    matching_clothes: List[ClothMatchItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ClothMatchRequest(BaseModel):
    matched_cloth_ids: List[int] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Wear Analytics schemas (Milestone 3)
# ---------------------------------------------------------------------------
class WearLogBase(BaseModel):
    worn_date: date


class BatchLogCreate(BaseModel):
    cloth_ids: List[int] = Field(..., min_length=1)
    worn_date: date


class WearLogResponse(WearLogBase):
    id: int
    cloth_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarDayResponse(BaseModel):
    date: date
    items: List[ClothResponse]


class RotationSuggestionsResponse(BaseModel):
    forgotten_favorites: List[ClothResponse]
    hidden_gems: List[ClothResponse]


# ---------------------------------------------------------------------------
# Look Collection schemas (Milestone 5)
# ---------------------------------------------------------------------------
class LookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    cloth_ids: List[int] = Field(..., min_length=1)


class LookResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    clothes: List[ClothResponse]

    model_config = ConfigDict(from_attributes=True)