"""
services.py
-----------
Business logic layer.  All domain-level computations live here,
keeping API routes thin and repositories focused on raw DB access.

Milestone 3 services:
  - RotationService  — 14-day wear rotation suggestion engine
"""

from datetime import date, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from repositories import WearLogRepository
from db_models import ClothModel


class RotationService:
    def __init__(self, db: Session):
        self.db = db
        self._repo = WearLogRepository(db)

    def get_suggested_clothes(self, user_id: int, threshold_days: int = 14) -> Dict[str, List[ClothModel]]:
        """
        Categorises active clothes into two rotation buckets:

        - hidden_gems:         Active items never logged (worn_date is None).
        - forgotten_favorites: Active items whose last log is older than `threshold_days` days ago.

        Items worn within the last `threshold_days` days appear in neither list.
        """
        cutoff_date = date.today() - timedelta(days=threshold_days)

        clothes_with_wear = self._repo.get_clothes_with_latest_wear(user_id)

        hidden_gems: List[ClothModel] = []
        forgotten_favorites: List[ClothModel] = []

        for cloth, latest_wear in clothes_with_wear:
            if latest_wear is None:
                hidden_gems.append(cloth)
            elif latest_wear < cutoff_date:
                forgotten_favorites.append(cloth)
            # else: worn recently — excluded from suggestions

        return {
            "hidden_gems": hidden_gems,
            "forgotten_favorites": forgotten_favorites,
        }
