from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/lists", tags=["Grocery Lists"])


def _enrich_list(lst: models.GroceryList) -> schemas.ListOut:
    """Add computed item_count and checked_count fields."""
    data = schemas.ListOut.model_validate(lst)
    data.item_count = len(lst.items)
    data.checked_count = sum(1 for i in lst.items if i.checked)
    return data


@router.get("/", response_model=list[schemas.ListOut])
def get_lists(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all grocery lists for the current user."""
    lists = (
        db.query(models.GroceryList)
        .filter(models.GroceryList.owner_id == current_user.id)
        .order_by(models.GroceryList.updated_at.desc())
        .all()
    )
    return [_enrich_list(lst) for lst in lists]


@router.post("/", response_model=schemas.ListOut, status_code=status.HTTP_201_CREATED)
def create_list(
    payload: schemas.ListCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new grocery list."""
    lst = models.GroceryList(**payload.model_dump(), owner_id=current_user.id)
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return _enrich_list(lst)


@router.get("/{list_id}", response_model=schemas.ListWithItems)
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get a specific list with all its items."""
    lst = _get_owned_list(list_id, current_user.id, db)
    result = schemas.ListWithItems.model_validate(lst)
    result.item_count = len(lst.items)
    result.checked_count = sum(1 for i in lst.items if i.checked)
    result.items = [schemas.ItemOut.model_validate(i) for i in lst.items]
    return result


@router.put("/{list_id}", response_model=schemas.ListOut)
def update_list(
    list_id: int,
    payload: schemas.ListUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update list name or description."""
    lst = _get_owned_list(list_id, current_user.id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lst, field, value)
    db.commit()
    db.refresh(lst)
    return _enrich_list(lst)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a list and all its items."""
    lst = _get_owned_list(list_id, current_user.id, db)
    db.delete(lst)
    db.commit()


def _get_owned_list(list_id: int, user_id: int, db: Session) -> models.GroceryList:
    lst = db.query(models.GroceryList).filter(
        models.GroceryList.id == list_id,
        models.GroceryList.owner_id == user_id,
    ).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    return lst
