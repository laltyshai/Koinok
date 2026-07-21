"""
db_models.py
------------
SQLAlchemy ORM models.  All domain tables are declared here.

Current models (Milestone 1):
  - UserModel  →  `users`  table
  - ClothModel →  `clothes` table

Subsequent milestones will ADD to this file (WearLog, Look, etc.)
without touching the existing definitions.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class UserModel(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False)
    email: str = Column(String, unique=True, index=True, nullable=False)
    hashed_password: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # One user → many clothes
    clothes = relationship("ClothModel", back_populates="owner")


# ---------------------------------------------------------------------------
# Cloth
# ---------------------------------------------------------------------------
class ClothModel(Base):
    __tablename__ = "clothes"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    name: str = Column(String, nullable=False)
    category: str = Column(String, nullable=False)  # validated at application layer
    is_deleted: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Many clothes → one user
    owner = relationship("UserModel", back_populates="clothes")
