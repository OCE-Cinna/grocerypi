"""
Database helper (repository) for the Product Catalog.

This file handles all database searches and updates for grocery products
(such as finding a product by its barcode, searching by name, or saving a
newly discovered product).
"""

from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import ItemCategory, PreferredStore, ProductCatalog
from app.schemas import ProductCatalogCreate


class ProductRepository:
    """Manages reading and saving products in the product_catalog database table."""

    @staticmethod
    def get_by_barcode(db: Session, barcode: str) -> Optional[ProductCatalog]:
        """Looks up a single product in the local database by its barcode."""
        clean_code = barcode.strip()
        return db.query(ProductCatalog).filter(ProductCatalog.barcode == clean_code).first()

    @staticmethod
    def list_products(
        db: Session,
        q: Optional[str] = None,
        category: Optional[ItemCategory] = None,
        preferred_store: Optional[PreferredStore] = None,
        limit: Optional[int] = None,
    ) -> List[ProductCatalog]:
        """
        Returns a list of products from the catalog.
        Can optionally filter by a search word (name, brand, or barcode),
        product category, or preferred supermarket.
        """
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

    @staticmethod
    def create(db: Session, payload: ProductCatalogCreate) -> ProductCatalog:
        """Saves a new product with all its nutrition details into the database."""
        product = ProductCatalog(**payload.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def create_fallback(db: Session, barcode: str) -> ProductCatalog:
        """
        Creates a basic placeholder product when a scanned barcode cannot be
        found in the Albert Heijn or Open Food Facts online databases.
        This ensures the user's scan is still saved and can be edited later.
        """
        clean_code = barcode.strip()
        product = ProductCatalog(
            barcode=clean_code,
            name=f"Scanned Item ({clean_code})",
            brand="Generic",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.OTHER,
            package_size="1 unit",
            is_dual_store=False,
            is_vegetarian=False,
            is_vegan=False,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
