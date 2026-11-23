"""
Database helper (repository) for Kitchen Inventory and Scan Logs.

This file handles all database operations for the items currently stored in the
kitchen (adding stock on scan, filtering by category or diet, sorting by
nutrients, changing quantities, deleting items, and saving scan history).
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.models import (
    InventoryItem,
    InventoryStatus,
    ItemCategory,
    PreferredStore,
    ProductCatalog,
    ScanLog,
    ScanStatus,
)
from app.schemas import InventoryItemUpdate


class InventoryRepository:
    """Manages reading and saving kitchen stock and barcode scan logs in the database."""

    # Columns that the user is allowed to sort the dashboard by
    ALLOWED_SORT_FIELDS = {
        "energy_kj": ProductCatalog.energy_kj,
        "energy_kcal": ProductCatalog.energy_kcal,
        "fat_grams": ProductCatalog.fat_grams,
        "saturated_fat_grams": ProductCatalog.saturated_fat_grams,
        "carbohydrate_grams": ProductCatalog.carbohydrate_grams,
        "sugar_grams": ProductCatalog.sugar_grams,
        "fiber_grams": ProductCatalog.fiber_grams,
        "protein_grams": ProductCatalog.protein_grams,
        "salt_grams": ProductCatalog.salt_grams,
        "nutriscore": ProductCatalog.nutriscore,
        "is_vegetarian": ProductCatalog.is_vegetarian,
        "is_vegan": ProductCatalog.is_vegan,
        "quantity": InventoryItem.quantity,
        "last_restocked_at": InventoryItem.last_restocked_at,
    }

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[InventoryItem]:
        """Finds a single inventory item in the database using its ID number."""
        return (
            db.query(InventoryItem)
            .options(joinedload(InventoryItem.product))
            .filter(InventoryItem.id == item_id)
            .first()
        )

    @staticmethod
    def get_by_product_id(db: Session, product_id: int) -> Optional[InventoryItem]:
        """Checks if a specific product is already in the kitchen inventory."""
        return db.query(InventoryItem).filter(InventoryItem.product_id == product_id).first()

    @classmethod
    def upsert_stock_on_scan(
        cls,
        db: Session,
        product_id: int,
        now_utc: datetime,
        default_interval_days: float = 7.0,
    ) -> InventoryItem:
        """
        Adds +1 to the product's quantity if it is already in stock, or creates
        a new inventory row with quantity 1 if it was not in the kitchen yet.
        """
        inv_item = cls.get_by_product_id(db, product_id)
        if inv_item:
            inv_item.quantity += 1
            inv_item.last_restocked_at = now_utc
            inv_item.status = InventoryStatus.IN_STOCK
        else:
            inv_item = InventoryItem(
                product_id=product_id,
                quantity=1,
                status=InventoryStatus.IN_STOCK,
                last_restocked_at=now_utc,
                restock_interval_days=default_interval_days,
            )
            db.add(inv_item)
        return inv_item

    @staticmethod
    def log_scan(
        db: Session,
        raw_barcode: str,
        product_id: Optional[int],
        status: ScanStatus,
        device_info: str,
        scanned_at: datetime,
    ) -> ScanLog:
        """Records a barcode scan event in the scan history table."""
        scan_log = ScanLog(
            raw_barcode=raw_barcode,
            product_id=product_id,
            status=status,
            device_info=device_info,
            scanned_at=scanned_at,
        )
        db.add(scan_log)
        return scan_log

    @classmethod
    def list_filtered(
        cls,
        db: Session,
        category: Optional[str] = None,
        preferred_store: Optional[PreferredStore] = None,
        item_status: Optional[InventoryStatus] = None,
        is_vegetarian: Optional[bool] = None,
        is_vegan: Optional[bool] = None,
        nutriscore: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: str = "desc",
    ) -> List[InventoryItem]:
        """
        Fetches the list of kitchen inventory items, applying any category, store,
        diet (vegan/vegetarian), or nutrient sorting chosen on the dashboard.
        """
        query = db.query(InventoryItem).join(ProductCatalog).options(joinedload(InventoryItem.product))

        if category:
            cat_lower = category.strip().lower()
            if cat_lower in ["pet", "pets"]:
                query = query.filter(ProductCatalog.category == ItemCategory.PET)
            elif cat_lower == "food":
                query = query.filter(ProductCatalog.category == ItemCategory.FOOD)
            elif cat_lower == "household":
                query = query.filter(ProductCatalog.category == ItemCategory.HOUSEHOLD)
            elif cat_lower == "hygiene":
                query = query.filter(ProductCatalog.category == ItemCategory.HYGIENE)
            else:
                query = query.filter(ProductCatalog.category == category)

        if preferred_store:
            query = query.filter(ProductCatalog.preferred_store == preferred_store)
        if item_status:
            query = query.filter(InventoryItem.status == item_status)
        if is_vegetarian is not None:
            query = query.filter(ProductCatalog.is_vegetarian == is_vegetarian)
        if is_vegan is not None:
            query = query.filter(ProductCatalog.is_vegan == is_vegan)
        if nutriscore:
            query = query.filter(ProductCatalog.nutriscore == nutriscore.strip().upper())

        if sort_by and sort_by in cls.ALLOWED_SORT_FIELDS:
            col = cls.ALLOWED_SORT_FIELDS[sort_by]
            query = query.order_by(desc(col) if order == "desc" else asc(col))
        else:
            query = query.order_by(desc(InventoryItem.last_restocked_at))

        return query.all()

    @staticmethod
    def list_stocked_with_products(db: Session) -> List[InventoryItem]:
        """Returns all inventory items that currently have at least 1 unit in stock."""
        return (
            db.query(InventoryItem)
            .join(ProductCatalog)
            .options(joinedload(InventoryItem.product))
            .filter(InventoryItem.quantity > 0)
            .all()
        )

    @staticmethod
    def update(db: Session, item: InventoryItem, payload: InventoryItemUpdate) -> InventoryItem:
        """
        Updates an item's quantity, stock status, dual-store flag, or custom
        restock interval days in the database.
        """
        if payload.quantity is not None:
            item.quantity = payload.quantity
            if item.quantity == 0:
                item.status = InventoryStatus.DEPLETED
            elif item.status == InventoryStatus.DEPLETED and item.quantity > 0:
                item.status = InventoryStatus.IN_STOCK

        if payload.status is not None:
            item.status = payload.status
        if payload.manual_interval_override is not None:
            item.manual_interval_override = payload.manual_interval_override
        if payload.is_dual_store is not None:
            item.is_dual_store = payload.is_dual_store

        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, item: InventoryItem) -> None:
        """Removes an item from the kitchen inventory table."""
        db.delete(item)
        db.commit()

    @staticmethod
    def list_recent_scans(db: Session, limit: int = 15) -> List[ScanLog]:
        """Returns the most recent barcode scans, newest first."""
        return db.query(ScanLog).order_by(desc(ScanLog.scanned_at)).limit(limit).all()
