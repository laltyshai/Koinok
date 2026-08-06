"""
db_models.py
------------
SQLAlchemy ORM models.  All domain tables are declared here.

Current models (Milestone 1 & 2):
  - UserModel  →  `users`  table
  - ClothModel →  `clothes` table

Milestone 3:
  - WearLogModel → `wear_logs` table
  
Subsequent milestones will ADD to this file (WearLog, Look, etc.)
without touching the existing definitions.
"""

from datetime import date, datetime, timezone, timedelta

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, String, UniqueConstraint, Index,
)
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
    category: str = Column(String, nullable=False, index=True)  # validated at application layer
    color: str = Column(String, nullable=True, index=True)
    season: str = Column(String, nullable=True, index=True)
    is_oversize: bool = Column(Boolean, nullable=True, default=False)
    is_deleted: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, default=datetime.now(timezone(timedelta(hours=6))))

    # Many clothes → one user
    owner = relationship("UserModel", back_populates="clothes")

    # One cloth → many wear logs (cascade delete-orphan)
    wear_logs = relationship(
        "WearLogModel",
        back_populates="cloth",
        cascade="all, delete-orphan",
        order_by="WearLogModel.worn_date.desc()",
    )


# ---------------------------------------------------------------------------
# WearLog  (Milestone 3)
# ---------------------------------------------------------------------------
class WearLogModel(Base):
    __tablename__ = "wear_logs"

    id: int = Column(Integer, primary_key=True, index=True)
    cloth_id: int = Column(Integer, ForeignKey("clothes.id", ondelete="CASCADE"), nullable=False, index=True)
    worn_date: date = Column(Date, nullable=False, index=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Many wear logs → one cloth
    cloth = relationship("ClothModel", back_populates="wear_logs")

    # Composite unique constraint: same item cannot be logged twice on same date
    __table_args__ = (
        UniqueConstraint("cloth_id", "worn_date", name="uq_cloth_worn_date"),
        Index("ix_wear_logs_cloth_worn", "cloth_id", "worn_date"),
    )

