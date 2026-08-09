"""
repositories.py
---------------
Data access repository layer for database operations.
Isolates database queries and soft-delete logic from API routes.
"""

from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from db_models import ClothModel, WearLogModel
import schemas


class ClothRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, cloth_in: schemas.ClothCreate, user_id: int) -> ClothModel:
        """Instantiates a new ClothModel record for user_id with default is_deleted=False."""
        category_val = cloth_in.category.value if hasattr(cloth_in.category, "value") else str(cloth_in.category)
        db_cloth = ClothModel(
            name=cloth_in.name,
            category=category_val,
            color=cloth_in.color,
            season=cloth_in.season,
            is_oversize=cloth_in.is_oversize,
            user_id=user_id,
            is_deleted=False,
        )
        self.db.add(db_cloth)
        self.db.commit()
        self.db.refresh(db_cloth)
        return db_cloth

    def get_by_id(self, cloth_id: int, user_id: int, include_deleted: bool = False) -> Optional[ClothModel]:
        """Queries a single clothing item scoped to user_id."""
        query = self.db.query(ClothModel).filter(
            ClothModel.id == cloth_id,
            ClothModel.user_id == user_id
        )
        if not include_deleted:
            query = query.filter(ClothModel.is_deleted == False)
        return query.first()

    def get_all_by_user(self, user_id: int, include_deleted: bool = False) -> Sequence[ClothModel]:
        """Retrieves all items belonging to user_id, ordered by newest first."""
        query = self.db.query(ClothModel).filter(ClothModel.user_id == user_id)
        if not include_deleted:
            query = query.filter(ClothModel.is_deleted == False)
        return query.order_by(ClothModel.created_at.desc()).all()

    def search(
        self,
        user_id: int,
        category: Optional[str] = None,
        color: Optional[str] = None,
        season: Optional[str] = None,
        is_oversize: Optional[bool] = None,
    ) -> Sequence[ClothModel]:
        """Dynamically filters active items belonging to user_id by any combination of criteria."""
        query = self.db.query(ClothModel).filter(
            ClothModel.user_id == user_id,
            ClothModel.is_deleted == False,
        )
        if category is not None:
            query = query.filter(ClothModel.category == category)
        if color is not None:
            query = query.filter(ClothModel.color == color)
        if season is not None:
            query = query.filter(ClothModel.season == season)
        if is_oversize is not None:
            query = query.filter(ClothModel.is_oversize == is_oversize)
        return query.order_by(ClothModel.created_at.desc()).all()

    def soft_delete(self, cloth: ClothModel) -> ClothModel:
        """Sets target ClothModel's is_deleted flag to True."""
        cloth.is_deleted = True
        self.db.commit()
        self.db.refresh(cloth)
        return cloth

    def restore(self, cloth: ClothModel) -> ClothModel:
        """Reverts target ClothModel's is_deleted flag back to False."""
        cloth.is_deleted = False
        self.db.commit()
        self.db.refresh(cloth)
        return cloth


class WearLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def batch_log_day(
        self,
        cloth_ids: List[int],
        user_id: int,
        worn_date: date,
    ) -> List[WearLogModel]:
        """
        Validates that all cloth_ids belong to user_id and are active,
        then bulk-inserts new WearLogModel records (skipping duplicates).
        Returns the newly created log entities.
        """
        # Validate ownership and active status
        valid_clothes = (
            self.db.query(ClothModel)
            .filter(
                ClothModel.id.in_(cloth_ids),
                ClothModel.user_id == user_id,
                ClothModel.is_deleted == False,
            )
            .all()
        )
        valid_ids = {c.id for c in valid_clothes}
        invalid = set(cloth_ids) - valid_ids
        if invalid:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or deleted cloth_ids: {sorted(invalid)}",
            )

        # Find already-existing logs on this date to avoid duplicates
        existing_logs = (
            self.db.query(WearLogModel.cloth_id)
            .filter(
                WearLogModel.cloth_id.in_(cloth_ids),
                WearLogModel.worn_date == worn_date,
            )
            .all()
        )
        existing_cloth_ids = {row.cloth_id for row in existing_logs}

        # Insert only new logs
        new_logs = []
        for cid in cloth_ids:
            if cid not in existing_cloth_ids:
                log = WearLogModel(cloth_id=cid, worn_date=worn_date)
                self.db.add(log)
                new_logs.append(log)

        self.db.commit()
        for log in new_logs:
            self.db.refresh(log)

        return new_logs

    def get_calendar_logs(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WearLogModel]:
        """
        Fetches all wear logs for active clothes belonging to user_id.
        Optionally filtered by date range. Returns logs sorted by worn_date desc.
        """
        query = (
            self.db.query(WearLogModel)
            .join(ClothModel, WearLogModel.cloth_id == ClothModel.id)
            .filter(
                ClothModel.user_id == user_id,
                ClothModel.is_deleted == False,
            )
        )
        if start_date:
            query = query.filter(WearLogModel.worn_date >= start_date)
        if end_date:
            query = query.filter(WearLogModel.worn_date <= end_date)

        return query.order_by(WearLogModel.worn_date.desc()).all()

    def get_clothes_with_latest_wear(
        self, user_id: int
    ) -> List[Tuple[ClothModel, Optional[date]]]:
        """
        Returns a list of (ClothModel, max_worn_date) tuples for all active
        clothes of the user. max_worn_date is None for never-worn items.
        """
        results = (
            self.db.query(ClothModel, func.max(WearLogModel.worn_date).label("latest_wear"))
            .outerjoin(WearLogModel, ClothModel.id == WearLogModel.cloth_id)
            .filter(
                ClothModel.user_id == user_id,
                ClothModel.is_deleted == False,
            )
            .group_by(ClothModel.id)
            .all()
        )
        return [(cloth, latest_wear) for cloth, latest_wear in results]
