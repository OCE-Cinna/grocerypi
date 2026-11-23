"""
API routes for managing kitchen inventory, nutrition totals, and shopping suggestions.

This file receives web requests from the React screen and passes them to the
matching background services (InventoryService, NutritionService, and PredictionEngine).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InventoryStatus, PreferredStore
from app.schemas import (
    BarcodeScanRequest,
    BarcodeScanResponse,
    CartSuggestionsResponse,
    InventoryItemOut,
    InventoryItemUpdate,
    NutritionalSummaryOut,
    ScanLogOut,
)
from app.services.inventory.inventory import inventory_service
from app.services.nutrition.nutrition import nutrition_service
from app.services.prediction.prediction import prediction_engine

router = APIRouter(prefix="/inventory", tags=["Inventory & Barcode Scanner"])


@router.post("/scan", response_model=BarcodeScanResponse, status_code=status.HTTP_200_OK)
def ingest_barcode_scan(payload: BarcodeScanRequest, db: Session = Depends(get_db)):
    """Receives a scanned barcode and adds +1 of that product to the kitchen stock."""
    return inventory_service.ingest_scan(
        db=db,
        barcode=payload.barcode,
        device_info=payload.device_info or "Raspberry Pi Camera v3",
        allow_fallback_creation=payload.confirm_unknown,
    )


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
        description="Field to sort by, such as protein_grams, sugar_grams, energy_kcal, or nutriscore.",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Returns the list of items currently in the kitchen, with optional filters and sorting."""
    return inventory_service.list_inventory(
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


@router.get("/nutrition/summary", response_model=NutritionalSummaryOut)
def get_nutrition_summary(db: Session = Depends(get_db)):
    """Returns the combined nutrition numbers and average Nutri-Score for all stocked items."""
    return nutrition_service.get_pantry_summary(db)


@router.get("/cart/suggestions", response_model=CartSuggestionsResponse)
def get_cart_suggestions(db: Session = Depends(get_db)):
    """Returns the suggested shopping lists for Albert Heijn, Jumbo, and Lidl."""
    return prediction_engine.get_cart_replenishment_suggestions(db)


@router.post("/sync/ah", status_code=status.HTTP_200_OK)
def trigger_ah_invoice_sync():
    """Reads saved Albert Heijn receipts to update product purchase history and predictions."""
    from app.db.parse_ah_invoices import seed_database
    seed_database()
    return {"status": "success", "message": "AH invoice sync and prediction seeding completed successfully."}


@router.patch("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(item_id: int, payload: InventoryItemUpdate, db: Session = Depends(get_db)):
    """Updates an item's quantity (when tapping + or -) or changes its restock settings."""
    return inventory_service.update_item(db, item_id, payload)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """Deletes an item completely from the current kitchen inventory."""
    inventory_service.delete_item(db, item_id)
    return None


@router.get("/scans/recent", response_model=List[ScanLogOut])
def get_recent_scans(limit: int = 15, db: Session = Depends(get_db)):
    """Returns a list of the most recent barcode scans."""
    return inventory_service.get_recent_scans(db, limit=limit)
