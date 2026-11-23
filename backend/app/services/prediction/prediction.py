"""
Shopping list prediction service for GroceryPi.

Instead of asking users to scan items when they throw them away, this file
estimates when products will run out based on how many days have passed since
they were last scanned in, and groups items that need restocking by store
(Albert Heijn, Jumbo, and Lidl).
"""

from datetime import datetime, timedelta, timezone
import re
from typing import List, Optional
from sqlalchemy.orm import Session

from app import models, schemas


class PredictionEngine:
    """Calculates which kitchen items are running low and sorts them into store shopping lists."""

    @staticmethod
    def compute_predicted_depletion_at(
        last_restocked_at: datetime,
        effective_interval_days: float,
        quantity: int = 1,
    ) -> datetime:
        """
        Calculates the predicted date and time when the current stock of an item
        will run out: last_restocked_at + timedelta(days=effective_interval * quantity).
        """
        base_dt = (
            last_restocked_at
            if last_restocked_at.tzinfo is not None
            else last_restocked_at.replace(tzinfo=timezone.utc)
        )
        total_days = max(1.0, float(effective_interval_days or 7.0)) * max(1, int(quantity or 1))
        return base_dt + timedelta(days=total_days)

    @staticmethod
    def calculate_empirical_interval_days(
        db: Session,
        product_id: int,
        current_interval: float = 7.0,
    ) -> float:
        """
        Calculates an item's rolling restock interval in days from historical
        ScanLog and PurchaseOrder timestamps for that product_id.
        """
        timestamps: List[datetime] = []

        scan_rows = (
            db.query(models.ScanLog.scanned_at)
            .filter(
                models.ScanLog.product_id == product_id,
                models.ScanLog.status == models.ScanStatus.SUCCESS,
            )
            .order_by(models.ScanLog.scanned_at.asc())
            .all()
        )
        for (dt,) in scan_rows:
            if dt:
                timestamps.append(dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc))

        order_rows = (
            db.query(models.PurchaseOrder.order_date)
            .join(models.PurchaseOrderItem, models.PurchaseOrderItem.order_id == models.PurchaseOrder.id)
            .filter(models.PurchaseOrderItem.product_id == product_id)
            .order_by(models.PurchaseOrder.order_date.asc())
            .all()
        )
        for (dt,) in order_rows:
            if dt:
                timestamps.append(dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc))

        timestamps.sort()
        # Collapse same-day timestamps so multi-pack scans on the same day count as one restock event
        distinct_days: List[datetime] = []
        for dt in timestamps:
            if not distinct_days or dt.astimezone().date() != distinct_days[-1].astimezone().date():
                distinct_days.append(dt)

        if len(distinct_days) < 2:
            return round(float(current_interval or 7.0), 1)

        gaps = [
            max(1.0, min(180.0, (distinct_days[i] - distinct_days[i - 1]).total_seconds() / 86400.0))
            for i in range(1, len(distinct_days))
        ]
        observed_avg = sum(gaps) / len(gaps)
        base = float(current_interval or observed_avg)
        return round(0.7 * base + 0.3 * observed_avg, 1)

    def get_cart_replenishment_suggestions(
        self,
        db: Session,
        reference_time: Optional[datetime] = None,
    ) -> schemas.CartSuggestionsResponse:
        """
        Checks all inventory items, compares how many days have passed since the
        last scan against how long the item usually lasts, and builds recommended
        shopping queues for AH, Jumbo, and Lidl.
        """
        now = reference_time or datetime.now(timezone.utc)

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

            # Use the user's custom restock days if set; otherwise use the learned average
            effective_interval = (
                item.manual_interval_override
                if item.manual_interval_override is not None
                else item.restock_interval_days
            )

            item_dt = item.last_restocked_at
            if item_dt and item_dt.tzinfo is None:
                item_dt = item_dt.replace(tzinfo=timezone.utc)
            cur_now = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)

            days_elapsed = max(0.0, (cur_now - item_dt).total_seconds() / 86400.0) if item_dt else 0.0

            pkg = prod.package_size or "unit"
            qty_suggested = max(1, item.quantity)
            quantity_text = f"{qty_suggested} × {pkg}" if pkg != "unit" else f"{qty_suggested} units"

            # Check how close the item is to running out
            interval_ratio = days_elapsed / max(1.0, effective_interval)
            needs_replenish = item.quantity <= 1 or interval_ratio >= 0.65

            if not needs_replenish:
                continue

            if item.status == models.InventoryStatus.DEPLETED or item.quantity == 0:
                urgency = "high"
                status_text = "synced / depleted · waiting to scan in"
            elif interval_ratio >= 1.0:
                urgency = "high"
                status_text = "due now · replenish"
            elif interval_ratio >= 0.75:
                urgency = "medium"
                status_text = "due soon"
            else:
                urgency = "normal"
                status_text = "next shop"

            subtext = f"Usually scanned every {int(round(effective_interval))} days · {status_text}"

            # Clean store names from the product title so the card stays easy to read
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

            # Place the suggested item into the right supermarket list (Jumbo, Lidl, or AH)
            if (item.is_dual_store or prod.is_dual_store) and prod.category in [
                models.ItemCategory.HOUSEHOLD,
                models.ItemCategory.HYGIENE,
            ]:
                sug.store = "Jumbo"
                jumbo_items.append(sug)
            elif "haver" in prod.name.lower() or "oats" in prod.name.lower() or prod.preferred_store == models.PreferredStore.LIDL:
                sug.store = "Lidl"
                lidl_items.append(sug)
            elif (item.is_dual_store or prod.is_dual_store) and len(jumbo_items) < 2 and prod.category == models.ItemCategory.FOOD:
                sug.store = "Jumbo"
                jumbo_items.append(sug)
            else:
                sug.store = "AH"
                ah_items.append(sug)

        # Put the most urgent items at the top of each store list
        urgency_order = {"high": 0, "medium": 1, "normal": 2}
        ah_items.sort(key=lambda x: urgency_order.get(x.urgency, 3))
        jumbo_items.sort(key=lambda x: urgency_order.get(x.urgency, 3))
        lidl_items.sort(key=lambda x: urgency_order.get(x.urgency, 3))

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


# Shared prediction engine instance
prediction_engine = PredictionEngine()


def get_cart_replenishment_suggestions(
    db: Session,
    reference_time: Optional[datetime] = None,
) -> schemas.CartSuggestionsResponse:
    """Helper function that calls the shared PredictionEngine to get shopping suggestions."""
    return prediction_engine.get_cart_replenishment_suggestions(db, reference_time=reference_time)
