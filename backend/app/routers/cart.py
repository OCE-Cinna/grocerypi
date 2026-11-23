"""
API routes for Supermarket Shopping Cart suggestions, Store App connections, and Cart Sync.

This file handles:
- GET /cart/suggestions: Returns recommended restock lists grouped by Albert Heijn, Jumbo, and Lidl.
- GET /cart/stores/status: Reports which supermarket mobile/web applications are connected
  (beyond anonymous catalog lookup) so the top Navbar can display 'AH Connected',
  'Jumbo Connected', 'AH & Jumbo', or 'Not connected'.
- POST /cart/stores/connect/{store}: Connects or toggles a supermarket app integration
  (using direct web/app deep-link list sync so user accounts are never banned for botting).
- POST /cart/sync/{store}: Syncs recommended items for the chosen supermarket via its
  IStoreGateway implementation and marks those items as DEPLETED (0 units) on the Dashboard.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, Set
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.clients.ah_gateway import AHStoreGateway, JumboStoreGateway
from app.clients.off_client import OpenFoodFactsClient
from app.database import get_db
from app.db.repositories.inventory_repository import InventoryRepository
from app.services.inventory.inventory import inventory_service
from app.services.prediction.prediction import prediction_engine

router = APIRouter(prefix="/cart", tags=["Supermarket Cart & Store Sync"])

# Tracks which supermarket apps are actively linked for cart/list syncing
_CONNECTED_STORES: Set[str] = set()
if os.getenv("AH_APP_CONNECTED", "false").lower() in ("true", "1", "yes"):
    _CONNECTED_STORES.add("AH")
if os.getenv("JUMBO_APP_CONNECTED", "false").lower() in ("true", "1", "yes"):
    _CONNECTED_STORES.add("Jumbo")


def _format_stores_status() -> Dict[str, Any]:
    """Formats the active supermarket connection status for the top Navbar."""
    ordered = [s for s in ("AH", "Jumbo") if s in _CONNECTED_STORES]
    if len(ordered) == 2:
        label = "AH & Jumbo"
    elif len(ordered) == 1:
        label = f"{ordered[0]} Connected"
    else:
        label = "Not connected"

    return {
        "connected": len(ordered) > 0,
        "connected_stores": ordered,
        "label": label,
        "sync_mode": "Direct Web & Mobile App List Deep-Link (Anti-Ban Safe)",
    }


@router.get("/suggestions", response_model=schemas.CartSuggestionsResponse)
def get_cart_suggestions(db: Session = Depends(get_db)):
    """Returns recommended shopping lists grouped by supermarket (AH, Jumbo, and Lidl)."""
    return prediction_engine.get_cart_replenishment_suggestions(db)


@router.get("/stores/status")
def get_stores_connection_status():
    """Returns which supermarket mobile/web applications are connected for cart syncing."""
    return _format_stores_status()


@router.post("/stores/connect/{store}")
def toggle_store_connection(store: str):
    """
    Connects or disconnects a supermarket application (AH or Jumbo) for direct
    web/mobile shopping list synchronization.
    """
    clean = store.strip()
    normalized = "AH" if clean.upper() == "AH" else "Jumbo" if clean.lower() == "jumbo" else clean
    if normalized not in ("AH", "Jumbo"):
        raise HTTPException(status_code=400, detail="Only AH and Jumbo support direct app/web cart sync.")

    if normalized in _CONNECTED_STORES:
        _CONNECTED_STORES.remove(normalized)
    else:
        _CONNECTED_STORES.add(normalized)

    return _format_stores_status()


@router.post("/sync/{store}")
def sync_store_cart(store: str, db: Session = Depends(get_db)):
    """
    Syncs the recommended items for a supermarket queue (AH, Jumbo, or Lidl)
    using its IStoreGateway implementation and marks those items as DEPLETED (0 units)
    so they are visually removed from the active Dashboard while staying in Cart
    Suggestions until physically scanned IN again.
    """
    clean = store.strip()
    normalized = (
        "AH"
        if clean.upper() == "AH"
        else "Jumbo"
        if clean.lower() == "jumbo"
        else "Lidl"
        if clean.lower() == "lidl"
        else clean
    )

    suggestions = prediction_engine.get_cart_replenishment_suggestions(db)
    target_queue = next(
        (q for q in suggestions.queues if q.id.lower() == normalized.lower()),
        None,
    )
    queue_items = (
        [{"id": i.id, "name": i.name, "quantity_text": i.quantity_text} for i in target_queue.items]
        if target_queue
        else []
    )

    if normalized == "AH":
        gateway = AHStoreGateway()
        _CONNECTED_STORES.add("AH")
    elif normalized == "Jumbo":
        gateway = JumboStoreGateway()
        _CONNECTED_STORES.add("Jumbo")
    else:
        gateway = OpenFoodFactsClient()

    gateway_result = gateway.sync_cart(queue_items)
    depletion_result = inventory_service.sync_store_cart(db, normalized)

    return {
        **depletion_result,
        "gateway_sync": gateway_result,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "stores_status": _format_stores_status(),
    }


@router.post("/restock/{item_id}", response_model=schemas.InventoryItemOut)
def mark_cart_item_bought_on_mobile(item_id: int, db: Session = Depends(get_db)):
    """
    Allows an authenticated mobile shopper in the supermarket aisle to tap
    'Bought / Restock' on a suggested cart item, immediately replenishing the
    item in grocerypi.db (IN_STOCK, quantity = 1) and updating its learned
    restock interval.
    """
    inv_item = InventoryRepository.get_by_id(db, item_id)
    if not inv_item:
        raise HTTPException(status_code=404, detail=f"Inventory item {item_id} not found")

    updated = InventoryRepository.upsert_stock_on_scan(
        db=db,
        product_id=inv_item.product_id,
        now_utc=datetime.now(timezone.utc),
    )
    db.commit()
    return InventoryRepository.get_by_id(db, updated.id)

