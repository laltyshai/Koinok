"""
routers/looks.py
-----------------
Look collections API router.
Bundles individual clothing items into named outfit collections.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import LookModel, UserModel
from security import get_current_user
from repositories import LookRepository
import schemas

router = APIRouter(prefix="/looks", tags=["Looks"])


def _to_response(look: LookModel) -> schemas.LookResponse:
    """Serializes a LookModel, excluding any soft-deleted clothes from the nested list."""
    active_clothes = [c for c in look.clothes if not c.is_deleted]
    return schemas.LookResponse(
        id=look.id,
        name=look.name,
        created_at=look.created_at,
        clothes=[schemas.ClothResponse.model_validate(c) for c in active_clothes],
    )


@router.post("/", response_model=schemas.LookResponse, status_code=status.HTTP_201_CREATED, summary="Create a Look from clothing items")
def create_look(
    look_in: schemas.LookCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Bundles the given cloth_ids into a single named Look owned by the authenticated user."""
    repo = LookRepository(db)
    look = repo.create_look(user_id=current_user.id, name=look_in.name, cloth_ids=look_in.cloth_ids)
    return _to_response(look)


@router.get("/", response_model=List[schemas.LookResponse], summary="List all saved Looks")
def get_user_looks(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Retrieves all Look collections belonging to the authenticated user."""
    repo = LookRepository(db)
    looks = repo.get_user_looks(user_id=current_user.id)
    return [_to_response(look) for look in looks]
