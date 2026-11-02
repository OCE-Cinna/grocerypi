from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from app.database import get_db
from app.models import ProductCatalog, InventoryItem, ScanLog, InventoryStatus, ScanStatus, ItemCategory, PreferredStore
from app.schemas import (
    InventoryItemOut,
    InventoryItemUpdate,
    BarcodeScanRequest,
    BarcodeScanResponse,
    NutritionalSummaryOut,
    ScanLogOut,
    CartSuggestionsResponse,
)
from app.services.prediction import get_cart_replenishment_suggestions

router = APIRouter(prefix="/inventory", tags=["Inventory & Barcode Scanner"])


# ─── Barcode Scan Ingestion ──────────────────────────────────────────────────

@router.post("/scan", response_model=BarcodeScanResponse, status_code=status.HTTP_200_OK)
def ingest_barcode_scan(payload: BarcodeScanRequest, db: Session = Depends(get_db)):
    """
    Ingests an optical barcode scan event (dispatched from Camera Module v3 or touch UI).
    Implements the 'Items IN' paradigm:
    - Automatically updates inventory quantity and updates last_restocked_at timestamp.
    - Records an audit log entry in scan_logs.
    """
    barcode = payload.barcode.strip()
    now_utc = datetime.now(timezone.utc)

    # 1. Look up item in catalog
    product = db.query(ProductCatalog).filter(ProductCatalog.barcode == barcode).first()

    if not product:
        # Audit unrecognized scan
        scan_log = ScanLog(
            raw_barcode=barcode,
            product_id=None,
            status=ScanStatus.UNKNOWN_BARCODE,
            device_info=payload.device_info or "Unknown",
            scanned_at=now_utc,
        )
        db.add(scan_log)
        db.commit()

        return BarcodeScanResponse(
            scan_status=ScanStatus.UNKNOWN_BARCODE,
            message=f"Barcode '{barcode}' not found in catalog. Please register product details.",
            scanned_at=now_utc,
            barcode=barcode,
            product=None,
            inventory_item=None,
        )

    # 2. Existing product recognized: Upsert inventory
    inv_item = db.query(InventoryItem).filter(InventoryItem.product_id == product.id).first()
    if inv_item:
        inv_item.quantity += 1
        inv_item.last_restocked_at = now_utc
        inv_item.status = InventoryStatus.IN_STOCK
    else:
        inv_item = InventoryItem(
            product_id=product.id,
            quantity=1,
            status=InventoryStatus.IN_STOCK,
            last_restocked_at=now_utc,
            restock_interval_days=7.0,
        )
        db.add(inv_item)

    # 3. Audit successful scan
    scan_log = ScanLog(
        raw_barcode=barcode,
        product_id=product.id,
        status=ScanStatus.SUCCESS,
        device_info=payload.device_info or "Raspberry Pi Camera v3",
        scanned_at=now_utc,
    )
    db.add(scan_log)
    db.commit()
    db.refresh(inv_item)

    return BarcodeScanResponse(
        scan_status=ScanStatus.SUCCESS,
        message=f"Successfully logged '{product.name}' into inventory (+1 unit).",
        scanned_at=now_utc,
        barcode=barcode,
        product=product,
        inventory_item=inv_item,
    )


# ─── Inventory List & Nutrient Autosort ──────────────────────────────────────

@router.get("", response_model=List[InventoryItemOut])
def get_inventory(
    category: Optional[str] = None,
    preferred_store: Optional[PreferredStore] = None,
    item_status: Optional[InventoryStatus] = None,
    is_vegetarian: Optional[bool] = None,
    is_vegan: Optional[bool] = None,
    nutriscore: Optional[str] = None,
    sort_by: Optional[str] = Query(
        None,
        description="Field to sort by: e.g. protein_grams, sugar_grams, energy_kcal, nutriscore, is_vegetarian, etc.",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    Lists household inventory items.
    Supports interactive autosorting and dietary filtering (vegetarian, vegan, nutriscore):
    - Sorts by any nutritional attribute or nutriscore.
    - Filters items by category, store, vegetarian, vegan, and nutriscore.
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

    # Nutritional & attribute sorting
    allowed_nutrition_fields = {
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

    if sort_by and sort_by in allowed_nutrition_fields:
        col = allowed_nutrition_fields[sort_by]
        query = query.order_by(desc(col) if order == "desc" else asc(col))
    else:
        # Default: newest restocked first
        query = query.order_by(desc(InventoryItem.last_restocked_at))

    return query.all()


# ─── Nutritional Aggregation Summary ──────────────────────────────────────────

@router.get("/nutrition/summary", response_model=NutritionalSummaryOut)
def get_nutrition_summary(db: Session = Depends(get_db)):
    """
    Calculates aggregated macros, energy, average Nutri-Score, and vegetarian/vegan counts
    across all currently stocked physical items for the Kiosk Nutritional Insights View.
    """
    items = db.query(InventoryItem).join(ProductCatalog).filter(InventoryItem.quantity > 0).all()

    summary = {
        "total_items_counted": 0,
        "total_energy_kj": 0.0,
        "total_energy_kcal": 0.0,
        "total_fat_grams": 0.0,
        "total_saturated_fat_grams": 0.0,
        "total_carbohydrate_grams": 0.0,
        "total_sugar_grams": 0.0,
        "total_fiber_grams": 0.0,
        "total_protein_grams": 0.0,
        "total_salt_grams": 0.0,
    }

    nutriscore_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
    reverse_map = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}
    nutriscore_weighted_sum = 0
    nutriscore_total_units = 0
    nutriscore_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    total_vegetarian = 0
    total_vegan = 0

    for item in items:
        p = item.product
        qty = item.quantity
        summary["total_items_counted"] += qty
        summary["total_energy_kj"] += p.energy_kj * qty
        summary["total_energy_kcal"] += p.energy_kcal * qty
        summary["total_fat_grams"] += p.fat_grams * qty
        summary["total_saturated_fat_grams"] += p.saturated_fat_grams * qty
        summary["total_carbohydrate_grams"] += p.carbohydrate_grams * qty
        summary["total_sugar_grams"] += p.sugar_grams * qty
        summary["total_fiber_grams"] += p.fiber_grams * qty
        summary["total_protein_grams"] += p.protein_grams * qty
        summary["total_salt_grams"] += p.salt_grams * qty

        # Mutually exclusive dietary counts to prevent double-counting:
        # Vegan items are pure plant-based.
        # Vegetarian items are non-vegan vegetarian (contains dairy/eggs).
        if p.is_vegan:
            total_vegan += qty
        elif p.is_vegetarian:
            total_vegetarian += qty

        if p.nutriscore and p.nutriscore.upper() in nutriscore_map:
            ns = p.nutriscore.upper()
            nutriscore_counts[ns] += qty
            nutriscore_weighted_sum += nutriscore_map[ns] * qty
            nutriscore_total_units += qty

    # Round macros to 2 decimal places
    for k in list(summary.keys()):
        if isinstance(summary[k], float):
            summary[k] = round(summary[k], 2)

    avg_numeric = round(nutriscore_weighted_sum / nutriscore_total_units, 2) if nutriscore_total_units > 0 else None
    avg_letter = None
    if avg_numeric is not None:
        rounded_val = min(5, max(1, round(avg_numeric)))
        avg_letter = reverse_map.get(rounded_val, "B")

    summary["average_nutriscore"] = avg_letter
    summary["average_nutriscore_numeric"] = avg_numeric
    summary["total_vegetarian_items"] = total_vegetarian
    summary["total_vegan_items"] = total_vegan
    summary["nutriscore_counts"] = nutriscore_counts

    return summary


# ─── Smart Replenishment & Cart Suggestions ───────────────────────────────────

@router.get("/cart/suggestions", response_model=CartSuggestionsResponse)
def get_cart_suggestions(db: Session = Depends(get_db)):
    """
    Computes suggested supermarket shopping replenishment queues (AH, Jumbo, Lidl)
    based on empirical restock intervals and the 'Items IN' prediction calculation.
    """
    return get_cart_replenishment_suggestions(db)


@router.post("/sync/ah", status_code=status.HTTP_200_OK)
def trigger_ah_invoice_sync():
    """
    Triggers re-parsing and seeding of Albert Heijn invoices from /home/grocerypi/Downloads/ah/.
    """
    from app.db.parse_ah_invoices import seed_database
    seed_database()
    return {"status": "success", "message": "AH invoice sync and prediction seeding completed successfully."}



# ─── Item Quantity & Status Adjustments ──────────────────────────────────────

@router.patch("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(item_id: int, payload: InventoryItemUpdate, db: Session = Depends(get_db)):
    """Adjusts inventory quantity (+/- touch buttons) or updates stock status."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found.")

    if payload.quantity is not None:
        item.quantity = payload.quantity
        if item.quantity == 0:
            item.status = InventoryStatus.DEPLETED

    if payload.status is not None:
        item.status = payload.status

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """Removes an item from current household inventory."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found.")

    db.delete(item)
    db.commit()
    return None


@router.get("/scans/recent", response_model=List[ScanLogOut])
def get_recent_scans(limit: int = 15, db: Session = Depends(get_db)):
    """Retrieves recent barcode scan activity for the kiosk feedback log."""
    return db.query(ScanLog).order_by(desc(ScanLog.scanned_at)).limit(limit).all()
