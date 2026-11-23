"""
Database helper (repository) for Kitchen Inventory and Scan Logs.

This file handles all database operations for the items currently stored in the
kitchen:
- Adding stock on scan with same-day batching vs. new-day (midnight 00:00) reset.
- Automatically depleting items once they reach their predicted interval or 30-day cap.
- Filtering by category or diet, sorting by nutrients, changing quantities,
  deleting items, and saving scan history.
"""

from datetime import datetime, timezone
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
        now_utc: Optional[datetime] = None,
        default_interval_days: float = 7.0,
    ) -> InventoryItem:
        """
        Updates stock when an item is scanned IN under the 'Items IN' lifecycle:
        - If the item was already scanned earlier on the SAME calendar day (before
          00:00 midnight) and is currently IN_STOCK, adds +1 to quantity so the
          user can scan multiple units bought in the same shopping trip.
        - If the item is scanned on a NEW calendar day (after 00:00 midnight) or
          was previously DEPLETED, treats the old batch as used/finished, updates
          the learned restock interval days from the time passed, and resets
          quantity to 1 for the new batch.
        """
        raw_now = now_utc or datetime.now(timezone.utc)
        cur_now = raw_now if raw_now.tzinfo is not None else raw_now.replace(tzinfo=timezone.utc)
        inv_item = cls.get_by_product_id(db, product_id)

        if inv_item:
            last_dt = inv_item.last_restocked_at
            if last_dt and last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)

            # Compare local calendar dates so the 24h cycle resets cleanly at 00:00 midnight
            same_calendar_day = (
                last_dt is not None
                and last_dt.astimezone().date() == cur_now.astimezone().date()
            )

            if same_calendar_day and inv_item.status == InventoryStatus.IN_STOCK and inv_item.quantity > 0:
                inv_item.quantity += 1
            else:
                # New calendar day or previously depleted: learn from elapsed days and reset batch to 1
                if last_dt is not None:
                    days_elapsed = max(0.0, (cur_now - last_dt).total_seconds() / 86400.0)
                    if days_elapsed >= 1.0:
                        observed_interval = min(30.0, max(1.0, days_elapsed))
                        old_interval = inv_item.restock_interval_days or default_interval_days
                        inv_item.restock_interval_days = round(
                            0.7 * old_interval + 0.3 * observed_interval, 1
                        )
                inv_item.quantity = 1

            inv_item.last_restocked_at = cur_now
            inv_item.status = InventoryStatus.IN_STOCK
        else:
            inv_item = InventoryItem(
                product_id=product_id,
                quantity=1,
                status=InventoryStatus.IN_STOCK,
                last_restocked_at=cur_now,
                restock_interval_days=default_interval_days,
            )
            db.add(inv_item)
        db.flush()
        return inv_item

    @classmethod
    def apply_auto_depletion(
        cls,
        db: Session,
        now_utc: Optional[datetime] = None,
        max_shelf_days: float = 30.0,
    ) -> int:
        """
        Automatically marks stocked items as DEPLETED (quantity = 0) once they reach
        their predicted restock interval or the 30-day maximum shelf limit.
        The item's learned restock_interval_days stays saved in the database while
        the item is visually hidden from the active Dashboard and moved to Cart Suggestions.
        """
        cur_now = now_utc or datetime.now(timezone.utc)
        if cur_now.tzinfo is None:
            cur_now = cur_now.replace(tzinfo=timezone.utc)

        active_items = (
            db.query(InventoryItem)
            .filter(InventoryItem.status == InventoryStatus.IN_STOCK)
            .all()
        )

        depleted_count = 0
        for item in active_items:
            last_dt = item.last_restocked_at
            if not last_dt:
                continue
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)

            days_elapsed = max(0.0, (cur_now - last_dt).total_seconds() / 86400.0)
            effective_interval = (
                item.manual_interval_override
                if item.manual_interval_override is not None
                else item.restock_interval_days
            )
            cutoff_days = min(max_shelf_days, max(1.0, effective_interval or 7.0))

            if days_elapsed >= cutoff_days:
                item.status = InventoryStatus.DEPLETED
                item.quantity = 0
                depleted_count += 1

        if depleted_count > 0:
            db.commit()
        return depleted_count

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
