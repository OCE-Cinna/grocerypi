"""
Replenishment & Prediction Engine for GroceryPi
Calculates consumption rates, dynamic depletion dates, and store replenishment queues
(AH, Jumbo, Lidl) based on empirical historical intervals and the 'Items IN' paradigm.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app import models, schemas


def get_cart_replenishment_suggestions(
    db: Session,
    reference_time: Optional[datetime] = None,
) -> schemas.CartSuggestionsResponse:
    """
    Computes suggested supermarket shopping queues based on empirical restock intervals,
    stock levels, and dual-store heuristics.
    """
    now = reference_time or datetime.now(timezone.utc)

    # Fetch inventory items with product catalog
    inv_items = (
        db.query(models.InventoryItem)
        .join(models.ProductCatalog)
        .all()
    )

    ah_items: List[schemas.CartSuggestionItem] = []
    jumbo_items: List[schemas.CartSuggestionItem] = []
    lidl_items: List[schemas.CartSuggestionItem] = []

    for item in inv_items:
        prod = item.product
        if not prod:
            continue

        effective_interval = item.manual_interval_override if item.manual_interval_override is not None else item.restock_interval_days
        
        item_dt = item.last_restocked_at
        if item_dt and item_dt.tzinfo is None:
            item_dt = item_dt.replace(tzinfo=timezone.utc)
        cur_now = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        
        days_elapsed = max(0.0, (cur_now - item_dt).total_seconds() / 86400.0) if item_dt else 0.0

        # Formatting quantity text (e.g. "2 × 1 L" or "1 × 500 g")
        pkg = prod.package_size or "unit"
        qty_suggested = max(1, item.quantity)
        quantity_text = f"{qty_suggested} × {pkg}" if pkg != "unit" else f"{qty_suggested} units"

        # Urgency threshold
        interval_ratio = days_elapsed / max(1.0, effective_interval)
        needs_replenish = item.quantity <= 1 or interval_ratio >= 0.65

        if not needs_replenish:
            continue

        # Urgency label & subtext
        if interval_ratio >= 1.0 or item.quantity == 0:
            urgency = "high"
            status_text = "due now · replenish"
        elif interval_ratio >= 0.75:
            urgency = "medium"
            status_text = "due soon"
        else:
            urgency = "normal"
            status_text = "next shop"

        subtext = f"Usually scanned every {int(round(effective_interval))} days · {status_text}"

        import re
        clean_name = re.sub(r"^(AH|Albert Heijn)\s+", "", prod.name, flags=re.IGNORECASE).strip()
        clean_name = re.sub(r"\s+\b(AH|Albert Heijn)\b", "", clean_name, flags=re.IGNORECASE).strip()

        brand_val = prod.brand
        if brand_val and brand_val.strip().lower() in ["ah", "albert heijn", "ah biologisch", "ah terra", "ah basic"]:
            brand_val = None
        if brand_val and brand_val.lower() in clean_name.lower():
            brand_val = None

        sug = schemas.CartSuggestionItem(
            id=item.id,
            store=prod.preferred_store.value if hasattr(prod.preferred_store, "value") else str(prod.preferred_store),
            name=clean_name,
            brand=brand_val,
            subtext=subtext,
            quantity_text=quantity_text,
            is_dual_store=bool(item.is_dual_store or prod.is_dual_store),
            effective_interval_days=round(effective_interval, 1),
            days_since_restock=round(days_elapsed, 1),
            current_quantity=item.quantity,
            urgency=urgency,
        )

        # Route to appropriate store queue
        # If dual-store and Household/Hygiene or named Dish soap/Dreft -> Jumbo queue
        if (item.is_dual_store or prod.is_dual_store) and prod.category in [models.ItemCategory.HOUSEHOLD, models.ItemCategory.HYGIENE]:
            sug.store = "Jumbo"
            jumbo_items.append(sug)
        elif "haver" in prod.name.lower() or "oats" in prod.name.lower() or prod.preferred_store == models.PreferredStore.LIDL:
            sug.store = "Lidl"
            lidl_items.append(sug)
        elif (item.is_dual_store or prod.is_dual_store) and len(jumbo_items) < 2 and prod.category == models.ItemCategory.FOOD:
            # Distribute some dual-store physical food items into Jumbo queue
            sug.store = "Jumbo"
            jumbo_items.append(sug)
        else:
            sug.store = "AH"
            ah_items.append(sug)

    # Sort each queue by urgency
    urgency_order = {"high": 0, "medium": 1, "normal": 2}
    ah_items.sort(key=lambda x: urgency_order.get(x.urgency, 3))
    jumbo_items.sort(key=lambda x: urgency_order.get(x.urgency, 3))
    lidl_items.sort(key=lambda x: urgency_order.get(x.urgency, 3))

    # Construct store queues matching Figma
    queues = [
        schemas.StoreQueue(
            id="AH",
            title=f"AH · {len(ah_items)} items",
            subtitle="Selected queue · sync AH only",
            items=ah_items,
        ),
        schemas.StoreQueue(
            id="Jumbo",
            title=f"Jumbo · {len(jumbo_items)} items",
            subtitle=f"{jumbo_items[0].name if jumbo_items else 'Physical purchases'} · separate sync",
            items=jumbo_items,
        ),
        schemas.StoreQueue(
            id="Lidl",
            title=f"Lidl · {len(lidl_items)} items",
            subtitle=f"{lidl_items[0].name if lidl_items else 'Pantry staples'} · separate list, no sync",
            items=lidl_items,
        ),
    ]

    return schemas.CartSuggestionsResponse(queues=queues)

