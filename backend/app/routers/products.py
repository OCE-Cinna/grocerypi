"""
API routes for searching and adding products in the master Product Catalog.

This file lets the frontend search known products by name or barcode and add
new product details to the local database.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db.repositories.product_repository import ProductRepository
from app.models import ItemCategory, PreferredStore
from app.schemas import ProductCatalogCreate, ProductCatalogOut, ProductCatalogUpdate

router = APIRouter(prefix="/products", tags=["Product Catalog"])


@router.get("", response_model=List[ProductCatalogOut])
def list_products(
    q: Optional[str] = Query(None, description="Search by product name, brand, or barcode"),
    category: Optional[ItemCategory] = None,
    preferred_store: Optional[PreferredStore] = None,
    limit: Optional[int] = Query(None, description="Maximum number of products to return"),
    db: Session = Depends(get_db),
):
    """Returns a list of products from the catalog matching the search query or filters."""
    return ProductRepository.list_products(
        db=db,
        q=q,
        category=category,
        preferred_store=preferred_store,
        limit=limit,
    )


@router.get("/{barcode}", response_model=ProductCatalogOut)
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """Looks up a single product's details using its barcode number."""
    product = ProductRepository.get_by_barcode(db, barcode)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode '{barcode}' not found in catalog.",
        )
    return product


@router.post("", response_model=ProductCatalogOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCatalogCreate, db: Session = Depends(get_db)):
    """Adds a new grocery product and its nutrition facts to the catalog."""
    existing = ProductRepository.get_by_barcode(db, payload.barcode)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with barcode '{payload.barcode}' already exists in catalog.",
        )
    return ProductRepository.create(db, payload)


@router.patch("/{barcode}", response_model=ProductCatalogOut)
def update_product(barcode: str, payload: ProductCatalogUpdate, db: Session = Depends(get_db)):
    """Updates a product's name, package size, or preferred supermarket by its barcode."""
    product = ProductRepository.get_by_barcode(db, barcode)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode '{barcode}' not found in catalog.",
        )
    return ProductRepository.update(db, product, payload)

