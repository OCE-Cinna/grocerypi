from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/lists/{list_id}/items", tags=["Items"])


def _get_owned_list(list_id: int, user_id: int, db: Session) -> models.GroceryList:
    lst = db.query(models.GroceryList).filter(
        models.GroceryList.id == list_id,
        models.GroceryList.owner_id == user_id,
    ).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    return lst


def _get_item(item_id: int, list_id: int, db: Session) -> models.Item:
    item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.list_id == list_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/", response_model=list[schemas.ItemOut])
def get_items(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all items in a grocery list."""
    _get_owned_list(list_id, current_user.id, db)
    return (
        db.query(models.Item)
        .filter(models.Item.list_id == list_id)
        .order_by(models.Item.created_at)
        .all()
    )


@router.post("/", response_model=schemas.ItemOut, status_code=status.HTTP_201_CREATED)
def add_item(
    list_id: int,
    payload: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add a new item to a grocery list."""
    _get_owned_list(list_id, current_user.id, db)
    item = models.Item(**payload.model_dump(), list_id=list_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.ItemOut)
def update_item(
    list_id: int,
    item_id: int,
    payload: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update an item (name, quantity, unit, or checked status)."""
    _get_owned_list(list_id, current_user.id, db)
    item = _get_item(item_id, list_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete an item from a grocery list."""
    _get_owned_list(list_id, current_user.id, db)
    item = _get_item(item_id, list_id, db)
    db.delete(item)
    db.commit()
