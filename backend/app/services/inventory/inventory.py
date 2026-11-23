"""
Core inventory service for GroceryPi.

This file manages the 'Items IN' workflow: whenever a barcode is scanned (either
by the physical Raspberry Pi camera or from the touch screen), this service
looks up the product, adds +1 to the kitchen stock, saves a scan history log,
and prepares the confirmation message shown on the screen.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Callable, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.db.repositories.inventory_repository import InventoryRepository
from app.db.repositories.product_repository import ProductRepository
from app.models import InventoryItem, InventoryStatus, PreferredStore, ScanLog, ScanStatus
from app.schemas import BarcodeScanResponse, InventoryItemUpdate
from app.services.ah_client import resolve_barcode_to_catalog_item

logger = logging.getLogger("grocerypi.services.inventory")


class InventoryService:
    """
    Handles all kitchen stock operations, including barcode scanning, listing
    filtered items, updating quantities, and deleting items.
    """

    def __init__(
        self,
        product_repo: type[ProductRepository] = ProductRepository,
        inventory_repo: type[InventoryRepository] = InventoryRepository,
        barcode_resolver: Callable[[str, Session], Any] = resolve_barcode_to_catalog_item,
    ):
        """Sets up the service with database helpers and the supermarket product lookup tool."""
        self.product_repo = product_repo
        self.inventory_repo = inventory_repo
        self.barcode_resolver = barcode_resolver
        self._latest_scan_event: Dict[str, Any] = {
            "scan_id": 0,
            "scan_status": None,
            "barcode": None,
            "product": None,
            "inventory_item": None,
            "timestamp": None,
            "message": None,
        }

    @property
    def latest_scan_event(self) -> Dict[str, Any]:
        """
        Returns the details of the most recent physical camera scan so the touch
        screen can show a 5-second confirmation pop-up.
        """
        return self._latest_scan_event

    def ingest_scan(
        self,
        db: Session,
        barcode: str,
        device_info: str = "Raspberry Pi Camera v3",
        allow_fallback_creation: bool = False,
    ) -> BarcodeScanResponse:
        """
        Processes a scanned barcode in 4 simple steps:
        1. Checks that the barcode is a valid retail number (8, 12, 13, or 14 digits)
           and checks if it is already saved in our local Product Catalog.
        2. If not in the local catalog, looks up the barcode online using Albert Heijn
           and Open Food Facts (Dutch/English only).
        3. If the product is still unknown, asks the user to confirm or redo the scan
           (unless allow_fallback_creation=True, which creates a custom item).
        4. Adds +1 to the item's quantity in the kitchen inventory and saves a scan log.
        """
        clean_code = barcode.strip()
        now_utc = datetime.now(timezone.utc)

        # Reject non-numeric or wrong-length reads caused by motion blur before querying
        if not clean_code.isdigit() or len(clean_code) not in (8, 12, 13, 14):
            self.inventory_repo.log_scan(
                db=db,
                raw_barcode=clean_code,
                product_id=None,
                status=ScanStatus.UNKNOWN_BARCODE,
                device_info=device_info,
                scanned_at=now_utc,
            )
            db.commit()
            return BarcodeScanResponse(
                scan_status=ScanStatus.UNKNOWN_BARCODE,
                message=f"Invalid barcode format ('{clean_code}'). Please hold the item steady and redo the scan.",
                scanned_at=now_utc,
                barcode=clean_code,
                product=None,
                inventory_item=None,
            )

        # Step 1: Check the local product catalog first
        product = self.product_repo.get_by_barcode(db, clean_code)

        # Step 2: If not found locally, check the Albert Heijn and Open Food Facts APIs
        if not product:
            try:
                product = self.barcode_resolver(clean_code, db)
            except Exception as resolve_err:
                logger.warning(f"Error resolving barcode '{clean_code}' from external API: {resolve_err}")

        # Step 3: Handle barcodes that were not found online
        is_synthetic_unknown = clean_code.startswith("9999999")
        if not product:
            if not allow_fallback_creation or is_synthetic_unknown:
                self.inventory_repo.log_scan(
                    db=db,
                    raw_barcode=clean_code,
                    product_id=None,
                    status=ScanStatus.UNKNOWN_BARCODE,
                    device_info=device_info,
                    scanned_at=now_utc,
                )
                db.commit()
                return BarcodeScanResponse(
                    scan_status=ScanStatus.UNKNOWN_BARCODE,
                    message=(
                        f"Barcode '{clean_code}' was not found in Albert Heijn or Open Food Facts. "
                        "Please redo the scan for a clearer read, or confirm to add it as a custom item."
                    ),
                    scanned_at=now_utc,
                    barcode=clean_code,
                    product=None,
                    inventory_item=None,
                )

            logger.info(f"User confirmed creating fallback catalog entry for barcode '{clean_code}'")
            product = self.product_repo.create_fallback(db, clean_code)

        # Step 4: Increase kitchen stock by +1 and save the scan in history
        inv_item = self.inventory_repo.upsert_stock_on_scan(
            db=db,
            product_id=product.id,
            now_utc=now_utc,
        )
        self.inventory_repo.log_scan(
            db=db,
            raw_barcode=clean_code,
            product_id=product.id,
            status=ScanStatus.SUCCESS,
            device_info=device_info,
            scanned_at=now_utc,
        )
        db.commit()
        db.refresh(inv_item)

        return BarcodeScanResponse(
            scan_status=ScanStatus.SUCCESS,
            message=f"Successfully logged '{product.name}' into inventory (+1 unit).",
            scanned_at=now_utc,
            barcode=clean_code,
            product=product,
            inventory_item=inv_item,
        )

    def handle_hardware_scan(self, barcode: str) -> None:
        """
        Runs automatically when the physical Raspberry Pi camera sees a barcode.
        It saves the scanned item using ingest_scan() and updates latest_scan_event
        so the touch screen immediately shows what was added.
        """
        logger.info(f"[HARDWARE SCANNER EVENT] Ingesting detected barcode: {barcode}")
        db: Session = SessionLocal()
        try:
            res = self.ingest_scan(
                db=db,
                barcode=barcode,
                device_info="Raspberry Pi Camera Module v3 (Optical Loop)",
                allow_fallback_creation=False,
            )
            now_utc = res.scanned_at
            product = res.product
            inv = res.inventory_item

            if res.scan_status == ScanStatus.SUCCESS and product and inv:
                self._latest_scan_event = {
                    "scan_id": int(now_utc.timestamp() * 1000),
                    "scan_status": "SUCCESS",
                    "barcode": res.barcode,
                    "device_info": "Raspberry Pi Camera Module v3 (Optical Loop)",
                    "product": {
                        "id": product.id,
                        "barcode": product.barcode,
                        "name": product.name,
                        "brand": product.brand,
                        "package_size": product.package_size,
                        "category": product.category.value if hasattr(product.category, "value") else str(product.category),
                        "nutriscore": product.nutriscore,
                        "is_vegan": product.is_vegan,
                        "is_vegetarian": product.is_vegetarian,
                    },
                    "inventory_item": {
                        "id": inv.id,
                        "product_id": inv.product_id,
                        "quantity": inv.quantity,
                        "status": inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                    },
                    "timestamp": now_utc.isoformat(),
                    "message": f"Added '{product.name}' (+1)",
                }
            else:
                self._latest_scan_event = {
                    "scan_id": int(now_utc.timestamp() * 1000),
                    "scan_status": "UNKNOWN_BARCODE",
                    "barcode": res.barcode,
                    "device_info": "Raspberry Pi Camera Module v3 (Optical Loop)",
                    "product": None,
                    "inventory_item": None,
                    "timestamp": now_utc.isoformat(),
                    "message": res.message,
                }
        except Exception as e:
            db.rollback()
            logger.error(f"[HARDWARE SCANNER] Error handling barcode {barcode}: {e}", exc_info=True)
        finally:
            db.close()

    def list_inventory(
        self,
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
        """Returns the list of kitchen inventory items filtered by category, diet, or sorted by nutrient."""
        return self.inventory_repo.list_filtered(
            db=db,
            category=category,
            preferred_store=preferred_store,
            item_status=item_status,
            is_vegetarian=is_vegetarian,
            is_vegan=is_vegan,
            nutriscore=nutriscore,
            sort_by=sort_by,
            order=order,
        )

    def update_item(self, db: Session, item_id: int, payload: InventoryItemUpdate) -> InventoryItem:
        """Changes an inventory item's quantity, status, or custom restock days, or returns 404 if missing."""
        item = self.inventory_repo.get_by_id(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found.")
        return self.inventory_repo.update(db, item, payload)

    def delete_item(self, db: Session, item_id: int) -> None:
        """Removes an item from the kitchen inventory, or returns 404 if the item does not exist."""
        item = self.inventory_repo.get_by_id(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found.")
        self.inventory_repo.delete(db, item)

    def get_recent_scans(self, db: Session, limit: int = 15) -> List[ScanLog]:
        """Returns the most recent barcode scans recorded by the system."""
        return self.inventory_repo.list_recent_scans(db, limit=limit)


# Shared instance used across the application
inventory_service = InventoryService()
