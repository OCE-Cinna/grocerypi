from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import ProductCatalog, ItemCategory, PreferredStore
from app.schemas import ProductCatalogCreate, ProductCatalogUpdate, ProductCatalogOut

router = APIRouter(prefix="/products", tags=["Product Catalog"])


@router.get("", response_model=List[ProductCatalogOut])
def list_products(
    q: Optional[str] = Query(None, description="Search by name, brand, or barcode"),
    category: Optional[ItemCategory] = None,
    preferred_store: Optional[PreferredStore] = None,
    limit: Optional[int] = Query(None, description="Max products to return"),
    db: Session = Depends(get_db),
):
    """Lists or searches products in the master catalog."""
    query = db.query(ProductCatalog)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                ProductCatalog.name.ilike(term),
                ProductCatalog.brand.ilike(term),
                ProductCatalog.barcode.like(term),
            )
        )
    if category:
        query = query.filter(ProductCatalog.category == category)
    if preferred_store:
        query = query.filter(ProductCatalog.preferred_store == preferred_store)
    if limit:
        query = query.limit(limit)

    return query.all()


@router.get("/{barcode}", response_model=ProductCatalogOut)
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """Fetches a single product specification by its EAN barcode."""
    product = db.query(ProductCatalog).filter(ProductCatalog.barcode == barcode.strip()).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode '{barcode}' not found in catalog.",
        )
    return product


@router.post("", response_model=ProductCatalogOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCatalogCreate, db: Session = Depends(get_db)):
    """Registers a new grocery product with full 9-field nutritional attributes."""
    existing = db.query(ProductCatalog).filter(ProductCatalog.barcode == payload.barcode.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with barcode '{payload.barcode}' already exists in catalog.",
        )

    product = ProductCatalog(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

