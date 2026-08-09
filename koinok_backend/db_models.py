"""
db_models.py
------------
SQLAlchemy ORM models.  All domain tables are declared here.

Current models (Milestone 1 & 2):
  - UserModel  →  `users`  table
  - ClothModel →  `clothes` table

Milestone 3:
  - WearLogModel → `wear_logs` table

Milestone 5:
  - matching_clothes → self-referential many-to-many association table on ClothModel
  - LookModel  →  `looks` table
  - look_items → many-to-many association table between LookModel and ClothModel

Subsequent milestones will ADD to this file without touching the existing definitions.
"""

from datetime import date, datetime, timezone, timedelta

from sqlalchemy import (
    and_, Boolean, Column, Date, DateTime, ForeignKey,
    Integer, String, Table, UniqueConstraint, Index,
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

    # One user → many looks
    looks = relationship("LookModel", back_populates="owner")


# ---------------------------------------------------------------------------
# Matchmaking association table (Milestone 5)
# ---------------------------------------------------------------------------
# Self-referential many-to-many: each row is a directed match link. The
# repository layer always writes both (A, B) and (B, A) in the same
# transaction so the relationship reads as symmetric.
matching_clothes_table = Table(
    "matching_clothes",
    Base.metadata,
    Column("cloth_id", Integer, ForeignKey("clothes.id", ondelete="CASCADE"), primary_key=True),
    Column("matched_cloth_id", Integer, ForeignKey("clothes.id", ondelete="CASCADE"), primary_key=True),
)


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

    # Self-referential many-to-many: items matched to this one (Milestone 5).
    # secondaryjoin also excludes soft-deleted targets so reciprocal match
    # results and Look payloads stay in sync with deletions automatically.
    matching_clothes = relationship(
        "ClothModel",
        secondary=matching_clothes_table,
        primaryjoin=id == matching_clothes_table.c.cloth_id,
        secondaryjoin=and_(id == matching_clothes_table.c.matched_cloth_id, is_deleted == False),
        viewonly=False,
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


# ---------------------------------------------------------------------------
# Look collections (Milestone 5)
# ---------------------------------------------------------------------------
look_items_table = Table(
    "look_items",
    Base.metadata,
    Column("look_id", Integer, ForeignKey("looks.id", ondelete="CASCADE"), primary_key=True),
    Column("cloth_id", Integer, ForeignKey("clothes.id", ondelete="CASCADE"), primary_key=True),
)


class LookModel(Base):
    __tablename__ = "looks"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Many looks → one user
    owner = relationship("UserModel", back_populates="looks")

    # Many-to-many: items bundled into this outfit
    clothes = relationship("ClothModel", secondary=look_items_table)

