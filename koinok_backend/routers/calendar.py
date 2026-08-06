"""
routers/calendar.py
-------------------
Calendar & Wear History API router.
Provides endpoints for daily outfit logging and historical calendar retrieval.
"""

from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import UserModel
from security import get_current_user
from repositories import WearLogRepository
import schemas

router = APIRouter(prefix="/calendar", tags=["Calendar & Wear History"])


@router.post(
    "/log-day",
    response_model=Dict[str, object],
    status_code=status.HTTP_201_CREATED,
    summary="Log multiple items worn on a specific date",
)
def log_day(
    payload: schemas.BatchLogCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Batch-logs one or more clothing items as worn on the given date.
    Duplicate entries (same item on same date) are silently skipped.
    """
    repo = WearLogRepository(db)
    new_logs = repo.batch_log_day(
        cloth_ids=payload.cloth_ids,
        user_id=current_user.id,
        worn_date=payload.worn_date,
    )
    return {
        "message": f"Logged {len(new_logs)} new wear entries for {payload.worn_date}",
        "logs": [schemas.WearLogResponse.model_validate(log) for log in new_logs],
    }


@router.get(
    "",
    response_model=List[schemas.CalendarDayResponse],
    summary="Get historical wear logs grouped by date",
)
def get_calendar(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Returns all wear logs for the authenticated user grouped by date.
    Accepts optional `start_date` and `end_date` query parameters for range filtering.
    """
    repo = WearLogRepository(db)
    logs = repo.get_calendar_logs(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )

    # Group logs by worn_date
    grouped: Dict[date, list] = defaultdict(list)
    for log in logs:
        grouped[log.worn_date].append(log.cloth)

    # Build sorted CalendarDayResponse list (newest date first)
    result = [
        schemas.CalendarDayResponse(
            date=day,
            items=[schemas.ClothResponse.model_validate(cloth) for cloth in clothes],
        )
        for day, clothes in sorted(grouped.items(), reverse=True)
    ]
    return result
