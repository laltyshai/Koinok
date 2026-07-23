"""
repositories.py
---------------
Data access repository layer for database operations.
Isolates database queries and soft-delete logic from API routes.
"""

from typing import Optional, Sequence
from sqlalchemy.orm import Session

from db_models import ClothModel
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