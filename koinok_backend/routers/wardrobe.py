"""
routers/wardrobe.py
-------------------
Wardrobe API router.
Provides endpoints for managing user's clothes, including soft-delete and restore.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from db_models import UserModel
from security import get_current_user
from repositories import ClothRepository
from services import RotationService
import schemas

router = APIRouter(prefix="/clothes", tags=["Wardrobe"])


@router.post("/", response_model=schemas.ClothResponse, status_code=status.HTTP_201_CREATED, summary="Create a new clothing item")
def create_cloth(
    cloth_in: schemas.ClothCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Creates a new item in the authenticated user's closet."""
    repo = ClothRepository(db)
    return repo.create(cloth_in, user_id=current_user.id)


@router.get("/", response_model=List[schemas.ClothResponse], summary="List all active clothing items")
def get_user_clothes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Retrieves all non-deleted clothing items belonging to the authenticated user."""
    repo = ClothRepository(db)
    return repo.get_all_by_user(user_id=current_user.id)


@router.get("/search", response_model=List[schemas.ClothResponse], summary="Search clothes by multi-criteria filters")
def search_clothes(
    category: Optional[schemas.ClothCategory] = None,
    color: Optional[str] = None,
    season: Optional[str] = None,
    is_oversize: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Filters the authenticated user's active clothes by any combination of category, color, season, and is_oversize."""
    repo = ClothRepository(db)
    return repo.search(
        user_id=current_user.id,
        category=category.value if category is not None else None,
        color=color,
        season=season,
        is_oversize=is_oversize,
    )


@router.get("/suggested", response_model=schemas.RotationSuggestionsResponse, summary="Get suggested unworn and forgotten clothes")
def get_suggested_clothes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Returns two lists: forgotten_favorites (not worn in 14+ days) and hidden_gems (never worn)."""
    service = RotationService(db)
    result = service.get_suggested_clothes(current_user.id)
    return schemas.RotationSuggestionsResponse(
        forgotten_favorites=result["forgotten_favorites"],
        hidden_gems=result["hidden_gems"],
    )


@router.get("/{cloth_id}", response_model=schemas.ClothResponse, summary="Get clothing item by ID")
def get_cloth_by_id(
    cloth_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Fetches a specific active item by ID. Raises 404 if missing or soft-deleted."""
    repo = ClothRepository(db)
    cloth = repo.get_by_id(cloth_id, user_id=current_user.id)
    if not cloth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found"
        )
    return cloth


@router.delete("/{cloth_id}", response_model=schemas.ClothResponse, summary="Soft delete clothing item")
def delete_cloth(
    cloth_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Soft deletes a clothing item. Raises 404 if missing or already soft-deleted."""
    repo = ClothRepository(db)
    cloth = repo.get_by_id(cloth_id, user_id=current_user.id)
    if not cloth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found"
        )
    return repo.soft_delete(cloth)


@router.post("/{cloth_id}/match", response_model=schemas.ClothResponse, summary="Link clothing items as bidirectional matches")
def match_cloth(
    cloth_id: int,
    match_in: schemas.ClothMatchRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Symmetrically links cloth_id with each id in matched_cloth_ids, returning the refreshed item."""
    repo = ClothRepository(db)
    cloth = repo.get_by_id(cloth_id, user_id=current_user.id)
    if not cloth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found"
        )
    return repo.add_matches(cloth, match_in.matched_cloth_ids, user_id=current_user.id)


@router.post("/{cloth_id}/restore", response_model=schemas.ClothResponse, summary="Restore soft-deleted item")
def restore_cloth(
    cloth_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Restores a soft-deleted clothing item back to active status."""
    repo = ClothRepository(db)
    cloth = repo.get_by_id(cloth_id, user_id=current_user.id, include_deleted=True)
    if not cloth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found"
        )
    if not cloth.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is not deleted"
        )
    return repo.restore(cloth)